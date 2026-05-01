from typing import Protocol, AsyncIterator
from app.modules.scraping.models import RawPost


class Scraper(Protocol):
    """Driven port: fetches raw posts from an external source.

    The single port for the scraping subdomain. Adapters per platform:
    TelegramScraper, FacebookScraper, OlxScraper, ...
    """

    async def fetch(self, source_name: str, limit: int = 50) -> AsyncIterator[RawPost]: ...
