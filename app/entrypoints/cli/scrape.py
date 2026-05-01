"""CLI: scrape Telegram channels into the listings DB.

Usage:
    python -m app.entrypoints.cli.scrape

Composition root for CLI: assembles concrete adapters and runs the use case.
"""
import asyncio
from telethon import TelegramClient

from app.infra.config import get_settings
from app.infra.db import SessionLocal, engine, Base
# import every module's orm so create_all sees them
from app.modules.listings.adapters import orm as _l  # noqa: F401
from app.modules.catalog.adapters import orm as _c  # noqa: F401
from app.modules.sources.adapters import orm as _s  # noqa: F401
from app.modules.users.adapters import orm as _u  # noqa: F401

from app.modules.listings.adapters.sqla_repository import SqlaListingRepository
from app.modules.sources.adapters.sqla_repository import SqlaSourceRepository
from app.modules.scraping.adapters.telegram_scraper import TelegramScraper
from app.modules.translation.adapters.anthropic_translator import AnthropicTranslator
from app.modules.scraping import import_telegram_posts


async def main() -> None:
    settings = get_settings()
    if not (settings.telegram_api_id and settings.telegram_api_hash):
        print("Set TELEGRAM_API_ID and TELEGRAM_API_HASH in .env")
        return
    if not settings.anthropic_api_key:
        print("Set ANTHROPIC_API_KEY in .env")
        return

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    translator = AnthropicTranslator(api_key=settings.anthropic_api_key)

    async with TelegramClient(
        settings.telegram_session, int(settings.telegram_api_id), settings.telegram_api_hash
    ) as tg_client:
        scraper = TelegramScraper(tg_client)
        async with SessionLocal() as session:
            try:
                count = await import_telegram_posts(
                    scraper=scraper,
                    sources_repo=SqlaSourceRepository(session),
                    listings_repo=SqlaListingRepository(session),
                    translator=translator,
                )
                await session.commit()
                print(f"Imported {count} new listings")
            except Exception:
                await session.rollback()
                raise


if __name__ == "__main__":
    asyncio.run(main())
