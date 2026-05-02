"""HTTP-скрейпер polovniautomobili.com — авто из Сербии и Черногории.

Driven adapter, реализует Scraper port. БЕЗ авторизации.

Стратегия:
- Тянем search page (HTML с встроенными JSON-LD блоками типа "Car")
- Парсим JSON-LD напрямую — проще и надёжнее чем HTML селекторы
- Каждая страница даёт ~25 объявлений
- Опционально углубляемся в детальную страницу за описанием/локацией/ценой

Polovni — сербский сайт, но с Montenegro-объявлениями. Фильтрация по городу/региону
делается на уровне детальной страницы (там видно `Crna Gora` в локации) — в search
JSON-LD location нет, поэтому первичный фильтр по тексту title.
"""
import json
import re
from datetime import datetime, timezone
from typing import AsyncIterator

import httpx
from bs4 import BeautifulSoup

from app.modules.scraping.models import RawPost, ScrapeError


SEARCH_URL = "https://www.polovniautomobili.com/auto-oglasi/pretraga"
USER_AGENT = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/120 Safari/537.36"


def _extract_cars(html: str) -> list[dict]:
    """Достаёт все Car-структуры из JSON-LD блоков на странице."""
    soup = BeautifulSoup(html, "html.parser")
    cars: list[dict] = []
    for sc in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(sc.string or "")
        except (ValueError, TypeError):
            continue
        # JSON-LD может быть объектом или массивом
        items = data if isinstance(data, list) else [data]
        for it in items:
            if isinstance(it, dict) and it.get("@type") == "Car":
                cars.append(it)
    return cars


def _car_to_raw(car: dict) -> RawPost | None:
    """Превращает Car-JSON-LD в RawPost."""
    url = (car.get("url") or "").strip()
    if not url:
        return None
    # external_id — последний числовой компонент url
    m = re.search(r"/(\d{6,})/", url)
    external_id = m.group(1) if m else url.rsplit("/", 1)[-1]

    brand = (car.get("brand") or "").strip()
    model = (car.get("model") or "").strip()
    year = (car.get("productionDate") or "").strip()
    title_parts = [p for p in (brand, model, year) if p]
    title = " ".join(title_parts) or "Auto"

    image = (car.get("image") or "").strip()
    image_urls = [image] if image and image.startswith("http") else []

    # Текст для downstream-парсера — он попробует выдрать цену/город регулярками
    description = "\n".join(filter(None, [
        f"{brand} {model}".strip(),
        f"Год: {year}" if year else None,
        f"Источник: {url}",
    ]))

    return RawPost(
        external_id=external_id,
        text=description if len(description) >= 30 else f"{title}\n{description}",
        posted_at=datetime.now(timezone.utc),
        image_urls=image_urls,
        source_url=url,
    )


class PolovniAutoScraper:
    """Driven adapter: тянет авто-объявления с polovniautomobili.com через JSON-LD."""

    def __init__(self, client: httpx.AsyncClient | None = None) -> None:
        self._client = client or httpx.AsyncClient(
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=20.0,
        )

    async def fetch(self, source_name: str, limit: int = 25) -> AsyncIterator[RawPost]:
        try:
            r = await self._client.get(SEARCH_URL)
        except httpx.HTTPError as e:
            raise ScrapeError(f"Polovni fetch failed: {e}") from e
        if r.status_code != 200:
            raise ScrapeError(f"Polovni HTTP {r.status_code}")

        cars = _extract_cars(r.text)
        emitted = 0
        for car in cars:
            if emitted >= limit:
                break
            post = _car_to_raw(car)
            if post is None:
                continue
            yield post
            emitted += 1

    async def close(self) -> None:
        await self._client.aclose()
