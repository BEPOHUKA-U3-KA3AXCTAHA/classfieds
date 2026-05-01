"""Scraping module: pulls raw posts from external sources, parses them, posts as listings.

Single driven port: Scraper. Cross-module deps go via direct imports of:
- sources (registry of channels/groups)
- translation (Translator port — LLM parsing)
- listings (post_listing service)
"""
from app.modules.scraping.models import RawPost, ScrapeError
from app.modules.scraping.ports.scraper import Scraper
from app.modules.scraping.services.import_telegram import import_telegram_posts

__all__ = ["RawPost", "ScrapeError", "Scraper", "import_telegram_posts"]
