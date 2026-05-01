from datetime import datetime, timezone
from typing import AsyncIterator

from telethon import TelegramClient

from app.modules.scraping.models import RawPost, ScrapeError


class TelegramScraper:
    """Driven adapter: implements Scraper port for public Telegram channels via MTProto.

    Constructed with a connected TelegramClient — wiring done in composition root
    (see adapters/cli/scrape.py or similar).
    """

    def __init__(self, client: TelegramClient) -> None:
        self._client = client

    async def fetch(self, source_name: str, limit: int = 50) -> AsyncIterator[RawPost]:
        try:
            async for msg in self._client.iter_messages(source_name, limit=limit):
                if not msg.text or len(msg.text) < 30:
                    continue
                yield RawPost(
                    external_id=str(msg.id),
                    text=msg.text,
                    posted_at=msg.date or datetime.now(timezone.utc),
                    image_urls=[],
                    source_url=f"https://t.me/{source_name}/{msg.id}",
                )
        except Exception as e:
            raise ScrapeError(f"Telegram scrape failed for {source_name}: {e}") from e
