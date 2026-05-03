"""CLI: scrape Telegram channels into the listings DB.

Usage:
    python -m app.entrypoints.cli.scrape              # auto-pick: MTProto если ключи есть, иначе HTTP
    python -m app.entrypoints.cli.scrape --http       # принудительно через HTTP-preview (без API)
    python -m app.entrypoints.cli.scrape --mtproto    # принудительно через Telethon (требует API_ID/HASH)

Composition root для CLI: собирает конкретные адаптеры и запускает use case.

Режимы:
- HTTP (без API): тянет публичные preview-страницы t.me/s/<channel>. Минусы — глубина 9-20 постов,
  только публичные каналы (не чаты), хрупко если поменяется HTML. Плюсы — ноль настройки, никаких ключей.
- MTProto (Telethon): полный API. Минусы — нужны TELEGRAM_API_ID/HASH (получить на my.telegram.org)
  + интерактивный логин на первом запуске (телефон + код). Плюсы — глубокая история, чаты, гарантия.

Если в .env нет ANTHROPIC_API_KEY — парсинг через LLM пропускается, посты сохраняются с минимальной
обработкой (заголовок = первая строка, описание = весь текст, ориг. язык = "ru").
"""
import asyncio
import sys

from app.infra.config import get_settings
from app.infra.db import SessionLocal, engine, Base
# import every module's orm so create_all sees them
from app.modules.listings.adapters import orm as _l  # noqa: F401
from app.modules.catalog.adapters import orm as _c  # noqa: F401
from app.modules.sources.adapters import orm as _s  # noqa: F401
from app.modules.users.adapters import orm as _u  # noqa: F401

from app.modules.listings.adapters.sqla_repository import SqlaListingRepository
from app.modules.sources.adapters.sqla_repository import SqlaSourceRepository
from app.modules.catalog.adapters.sqla_repository import SqlaCategoryRepository
from app.modules.scraping.adapters.http_telegram_scraper import HttpTelegramScraper
from app.modules.scraping import import_telegram_posts
from app.modules.translation.ports.translator import Translator
from app.modules.translation.models import ParsedListing


import re as _re

_PRICE_RE = _re.compile(
    r"(\d{1,3}(?:[\s ]?\d{3})*(?:[.,]\d+)?)\s*(€|eur|евро|euro)\b",
    _re.IGNORECASE,
)
_PHONE_RE = _re.compile(r"(?<!\d)(\+?\d[\d\s\-()]{8,16}\d)(?!\d)")
_TG_HANDLE_RE = _re.compile(r"@([a-z0-9_]{4,32})", _re.IGNORECASE)
_MN_CITIES = ["Podgorica", "Подгорица", "Budva", "Будва", "Kotor", "Котор",
              "Tivat", "Тиват", "Bar", "Бар", "Herceg Novi", "Херцег Нови",
              "Cetinje", "Цетинье", "Ulcinj", "Улцинь", "Niksic", "Никшич"]
_CITY_RE = _re.compile(r"\b(" + "|".join(_MN_CITIES) + r")\b", _re.IGNORECASE)


def _meaningful_first_line(text: str, max_len: int = 100) -> str:
    """Первая строка где есть >=4 буквенных символов (пропускает emoji/хештеги/линию из 📍)."""
    for line in text.strip().splitlines():
        line = line.strip().lstrip("#").strip()
        if sum(1 for c in line if c.isalpha()) >= 4:
            return line[:max_len]
    return text.strip().split("\n", 1)[0][:max_len] or "Объявление"


class _StubTranslator:
    """Эвристический Translator на случай отсутствия Anthropic ключа.

    Без LLM. Парсит регулярками: цена (EUR), телефон, telegram-handle, город.
    Заголовок — первая содержательная строка (не emoji-only, не хештег).
    """

    async def parse_post(self, raw_text: str) -> ParsedListing:
        text = raw_text.strip()
        title = _meaningful_first_line(text)

        price_amount = None
        if (m := _PRICE_RE.search(text)):
            num = m.group(1).replace(" ", "").replace(" ", "").replace(",", ".")
            try:
                price_amount = float(num)
            except ValueError:
                pass

        phone = None
        if (m := _PHONE_RE.search(text)):
            digits = "".join(c for c in m.group(1) if c.isdigit() or c == "+")
            if 9 <= len(digits.lstrip("+")) <= 15:
                phone = digits

        tg = None
        if (m := _TG_HANDLE_RE.search(text)):
            tg = m.group(1)

        city = None
        if (m := _CITY_RE.search(text)):
            raw_city = m.group(1).title()
            # нормализуем кириллицу в латиницу для единообразия в базе
            city_map = {
                "Подгорица": "Podgorica", "Будва": "Budva", "Котор": "Kotor",
                "Тиват": "Tivat", "Бар": "Bar", "Херцег Нови": "Herceg Novi",
                "Цетинье": "Cetinje", "Улцинь": "Ulcinj", "Никшич": "Niksic",
            }
            city = city_map.get(raw_city, raw_city)

        return ParsedListing(
            title=title,
            description=text,
            title_translations={"ru": title, "me": title, "en": title},
            original_lang="ru",
            price_amount=price_amount,
            price_currency="EUR" if price_amount else None,
            city=city,
            category_hint=None,
            contact_telegram=tg,
            contact_phone=phone,
        )

    async def translate_text(self, text: str, src_lang: str, dst_lang: str) -> str:
        return text


def _pick_mode(argv: list[str]) -> str:
    """Возвращает 'http' или 'mtproto'."""
    if "--http" in argv:
        return "http"
    if "--mtproto" in argv:
        return "mtproto"
    settings = get_settings()
    return "mtproto" if (settings.telegram_api_id and settings.telegram_api_hash) else "http"


async def _make_translator() -> Translator:
    settings = get_settings()
    if settings.anthropic_api_key:
        from app.modules.translation.adapters.anthropic_translator import AnthropicTranslator
        return AnthropicTranslator(api_key=settings.anthropic_api_key)
    print("  ! ANTHROPIC_API_KEY не задан — парсинг через эвристику (без LLM)")
    return _StubTranslator()


async def _run_telegram(mode: str, translator: Translator) -> int:
    from app.modules.sources import SourceType
    async with SessionLocal() as session:
        try:
            if mode == "http":
                scraper = HttpTelegramScraper()
                try:
                    count = await import_telegram_posts(
                        scraper=scraper,
                        sources_repo=SqlaSourceRepository(session),
                        listings_repo=SqlaListingRepository(session),
                        translator=translator,
                        categories_repo=SqlaCategoryRepository(session),
                        source_type=SourceType.TELEGRAM,
                    )
                finally:
                    await scraper.close()
            else:
                from telethon import TelegramClient
                from app.modules.scraping.adapters.telegram_scraper import TelegramScraper
                settings = get_settings()
                async with TelegramClient(
                    settings.telegram_session, int(settings.telegram_api_id), settings.telegram_api_hash
                ) as tg_client:
                    count = await import_telegram_posts(
                        scraper=TelegramScraper(tg_client),
                        sources_repo=SqlaSourceRepository(session),
                        listings_repo=SqlaListingRepository(session),
                        translator=translator,
                        categories_repo=SqlaCategoryRepository(session),
                        source_type=SourceType.TELEGRAM,
                    )
            await session.commit()
            return count
        except Exception:
            await session.rollback()
            raise


async def _run_mojkvadrat(translator: Translator) -> int:
    from app.modules.sources import SourceType
    from app.modules.scraping.adapters.mojkvadrat_scraper import MojkvadratScraper
    async with SessionLocal() as session:
        try:
            scraper = MojkvadratScraper()
            try:
                count = await import_telegram_posts(
                    scraper=scraper,
                    sources_repo=SqlaSourceRepository(session),
                    listings_repo=SqlaListingRepository(session),
                    translator=translator,
                    categories_repo=SqlaCategoryRepository(session),
                    source_type=SourceType.MOJKVADRAT,
                )
            finally:
                await scraper.close()
            await session.commit()
            return count
        except Exception:
            await session.rollback()
            raise


async def _run_polovni(translator: Translator) -> int:
    from app.modules.sources import SourceType
    from app.modules.scraping.adapters.polovni_auto_scraper import PolovniAutoScraper
    async with SessionLocal() as session:
        try:
            scraper = PolovniAutoScraper()
            try:
                count = await import_telegram_posts(
                    scraper=scraper,
                    sources_repo=SqlaSourceRepository(session),
                    listings_repo=SqlaListingRepository(session),
                    translator=translator,
                    categories_repo=SqlaCategoryRepository(session),
                    source_type=SourceType.POLOVNI,
                )
            finally:
                await scraper.close()
            await session.commit()
            return count
        except Exception:
            await session.rollback()
            raise


async def main(argv: list[str]) -> None:
    only = (
        "telegram" if "--only-telegram" in argv
        else "mojkvadrat" if "--only-mojkvadrat" in argv
        else "polovni" if "--only-polovni" in argv
        else "all"
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    translator = await _make_translator()

    total = 0
    if only in ("all", "telegram"):
        mode = _pick_mode(argv)
        print(f"  → telegram режим: {mode}")
        total += await _run_telegram(mode, translator)
    if only in ("all", "mojkvadrat"):
        print(f"  → mojkvadrat.me (HTTP)")
        total += await _run_mojkvadrat(translator)
    if only in ("all", "polovni"):
        print(f"  → polovniautomobili.com (JSON-LD)")
        total += await _run_polovni(translator)

    print(f"  ✓ импортировано новых объявлений всего: {total}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
