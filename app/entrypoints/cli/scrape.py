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
from app.modules.scraping.adapters.http_telegram_scraper import HttpTelegramScraper
from app.modules.scraping import import_telegram_posts
from app.modules.translation.ports.translator import Translator
from app.modules.translation.models import ParsedListing


class _StubTranslator:
    """Заглушка-Translator на случай отсутствия Anthropic ключа.

    Не делает реального LLM-парсинга и перевода — просто разбирает текст эвристически.
    Заголовок = первая строка (≤100 символов), описание = весь текст, lang = "ru" (большинство наших каналов).
    """

    async def parse_post(self, raw_text: str) -> ParsedListing:
        first = raw_text.strip().split("\n", 1)[0][:100] or "Объявление"
        return ParsedListing(
            title=first,
            description=raw_text.strip(),
            title_translations={"ru": first, "me": first, "en": first},
            original_lang="ru",
            price_amount=None,
            price_currency="EUR",
            city=None,
            category_hint=None,
            contact_telegram=None,
            contact_phone=None,
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


async def _run(mode: str, translator: Translator) -> int:
    """Открывает session и нужный scraper-адаптер; делает import и коммит."""
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
                    )
            await session.commit()
            return count
        except Exception:
            await session.rollback()
            raise


async def main(argv: list[str]) -> None:
    mode = _pick_mode(argv)
    print(f"  → режим: {mode}")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    translator = await _make_translator()
    count = await _run(mode, translator)
    print(f"  ✓ импортировано новых объявлений: {count}")


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1:]))
