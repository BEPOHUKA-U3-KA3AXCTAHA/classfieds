"""HTTP-скрейпер Telegram через публичные preview-страницы (https://t.me/s/<channel>).

Driven adapter, реализует Scraper port. НЕ требует API_ID/API_HASH — работает
без авторизации, тянет HTML preview-страницы канала и парсит через bs4.

Ограничения:
- только публичные каналы (с @username)
- видны только последние ~9-20 постов на preview странице
- HTML-структура t.me может меняться (хрупкость)
- Telegram может прибить за частые запросы — держим минимум 1-2 секунды между каналами

Альтернатива — TelegramScraper (Telethon, MTProto): глубже и надёжнее, но требует API-ключи и интерактивный логин.
"""
import asyncio
import re
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from bs4 import BeautifulSoup

from app.modules.scraping.models import RawPost, ScrapeError


PREVIEW_URL = "https://t.me/s/{channel}"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
MIN_TEXT_LEN = 30                # фильтр коротких/служебных постов
DEFAULT_DELAY_BETWEEN_CHANNELS = 2.0   # секунд


def _extract_photo_urls(message_wrap) -> list[str]:
    """Вытащить URL картинок из inline style: background-image:url('...')."""
    urls: list[str] = []
    for a in message_wrap.select(".tgme_widget_message_photo_wrap"):
        style = a.get("style", "")
        m = re.search(r"background-image:url\('([^']+)'\)", style)
        if m:
            urls.append(m.group(1))
    return urls


def _parse_post(wrap) -> RawPost | None:
    msg = wrap.select_one(".tgme_widget_message")
    if msg is None:
        return None
    data_post = msg.get("data-post", "")
    if "/" not in data_post:
        return None
    channel, raw_id = data_post.rsplit("/", 1)

    text_el = wrap.select_one(".tgme_widget_message_text")
    text = text_el.get_text("\n", strip=True) if text_el else ""
    if len(text) < MIN_TEXT_LEN:
        return None

    date_el = wrap.select_one("time[datetime]")
    if date_el is None:
        return None
    try:
        posted_at = datetime.fromisoformat(date_el["datetime"].replace("Z", "+00:00"))
    except (ValueError, KeyError):
        posted_at = datetime.now(timezone.utc)

    return RawPost(
        external_id=raw_id,
        text=text,
        posted_at=posted_at,
        image_urls=_extract_photo_urls(wrap),
        source_url=f"https://t.me/{channel}/{raw_id}",
    )


class HttpTelegramScraper:
    """Driven adapter: реализует Scraper через HTTP preview Telegram (без API)."""

    def __init__(
        self,
        client: httpx.AsyncClient | None = None,
        delay_between_channels: float = DEFAULT_DELAY_BETWEEN_CHANNELS,
    ) -> None:
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=15.0,
        )
        self._delay = delay_between_channels
        self._first_call_done = False

    async def fetch(self, source_name: str, limit: int = 50) -> AsyncIterator[RawPost]:
        # rate-limit между каналами в одной сессии
        if self._first_call_done and self._delay > 0:
            await asyncio.sleep(self._delay)
        self._first_call_done = True

        try:
            r = await self._client.get(PREVIEW_URL.format(channel=source_name))
        except httpx.HTTPError as e:
            raise ScrapeError(f"HTTP fetch failed for {source_name}: {e}") from e

        if r.status_code != 200:
            raise ScrapeError(f"{source_name}: HTTP {r.status_code}")

        soup = BeautifulSoup(r.text, "html.parser")
        wraps = soup.select(".tgme_widget_message_wrap")

        emitted = 0
        for w in wraps:
            if emitted >= limit:
                break
            post = _parse_post(w)
            if post is None:
                continue
            yield post
            emitted += 1

    async def close(self) -> None:
        await self._client.aclose()
