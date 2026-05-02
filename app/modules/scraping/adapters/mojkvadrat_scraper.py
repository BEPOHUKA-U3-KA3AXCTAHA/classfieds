"""HTTP-скрейпер mojkvadrat.me — недвижимость Черногории.

Driven adapter, реализует Scraper port. БЕЗ авторизации.

Особенность Mojkvadrat: нет sitemap.xml и нет публичного list-endpoint,
только home page с ~6 featured листингами + индивидуальные страницы.
Поэтому стратегия — забрать featured + углубиться в каждую страницу за деталями.

Порт `Scraper.fetch(source_name, limit)` ожидает имя источника. Для Mojkvadrat
любое значение — мы всё равно тянем home (структура сайта не даёт фильтра по подразделам без JS).
Используй имя 'home' или 'featured' — это просто метка для логов.
"""
import re
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from bs4 import BeautifulSoup

from app.modules.scraping.models import RawPost, ScrapeError


BASE = "https://www.mojkvadrat.me"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"
LISTING_HREF_RE = re.compile(r"^/?nekretnine/([a-z0-9-]+)/?$", re.IGNORECASE)


def _absolute(href: str) -> str:
    if href.startswith("http"):
        return href
    if href.startswith("/"):
        return BASE + href
    return f"{BASE}/{href}"


def _parse_listing_page(html: str, url: str, slug: str) -> RawPost | None:
    soup = BeautifulSoup(html, "html.parser")

    # заголовок — обычно h1
    h1 = soup.find("h1")
    title = h1.get_text(" ", strip=True) if h1 else slug.replace("-", " ").title()

    # описание — самый длинный текстовый блок (paragraph) на странице
    paragraphs = [p.get_text(" ", strip=True) for p in soup.find_all("p")]
    paragraphs = [p for p in paragraphs if len(p) > 30]
    description = "\n\n".join(paragraphs[:6]) if paragraphs else title

    # картинки — img с src на собственный домен или CDN, исключаем иконки/лого
    image_urls: list[str] = []
    for img in soup.find_all("img"):
        src = img.get("src") or img.get("data-src") or ""
        if not src:
            continue
        src_abs = _absolute(src)
        # пропускаем мелкие SVG/иконки
        if any(skip in src_abs.lower() for skip in ("logo", "icon", "favicon", "placeholder")):
            continue
        if not any(src_abs.lower().endswith(ext) for ext in (".jpg", ".jpeg", ".png", ".webp")):
            continue
        if src_abs not in image_urls:
            image_urls.append(src_abs)

    # пытаемся найти цену — €/EUR в тексте
    text = soup.get_text(" ", strip=True)
    price_match = re.search(r"(\d[\d\s.,]{2,})\s*(€|EUR|eur)\b", text, re.IGNORECASE)
    if price_match:
        # припишем к описанию для downstream-парсера если он пропустит
        pass

    # дата публикации почти никогда не доступна — берём now
    posted_at = datetime.now(timezone.utc)

    if not description.strip() or len(description) < 30:
        return None

    return RawPost(
        external_id=slug,
        text=f"{title}\n\n{description}",
        posted_at=posted_at,
        image_urls=image_urls[:8],
        source_url=url,
    )


class MojkvadratScraper:
    """Driven adapter: тянет недвижимость с mojkvadrat.me (HTML, без API)."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=20.0,
        )

    async def fetch(self, source_name: str, limit: int = 20) -> AsyncIterator[RawPost]:
        # достаём список slug-ов с главной
        try:
            r = await self._client.get(BASE)
        except httpx.HTTPError as e:
            raise ScrapeError(f"Mojkvadrat home fetch failed: {e}") from e

        if r.status_code != 200:
            raise ScrapeError(f"Mojkvadrat home returned HTTP {r.status_code}")

        soup = BeautifulSoup(r.text, "html.parser")
        slugs: list[str] = []
        seen = set()
        for a in soup.find_all("a", href=True):
            m = LISTING_HREF_RE.match(a["href"])
            if not m:
                continue
            slug = m.group(1)
            if slug in seen:
                continue
            seen.add(slug)
            slugs.append(slug)

        # для каждого slug — заходим на детальную и собираем карточку
        emitted = 0
        for slug in slugs:
            if emitted >= limit:
                break
            url = f"{BASE}/nekretnine/{slug}"
            try:
                rr = await self._client.get(url)
            except httpx.HTTPError:
                continue
            if rr.status_code != 200:
                continue
            post = _parse_listing_page(rr.text, url, slug)
            if post is None:
                continue
            yield post
            emitted += 1

    async def close(self) -> None:
        await self._client.aclose()
