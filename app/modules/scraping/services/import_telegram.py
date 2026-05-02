"""Orchestrator: pull raw posts from Telegram, parse via translator, post as listings.

Cross-module deps go via direct imports of other modules' public APIs:
- sources: SourceRepository (registry)
- translation: Translator (LLM-parsing)
- listings: post_listing (service)

Scraping module owns ONE driven port: Scraper.
"""
import hashlib
import re
from decimal import Decimal

from app.modules.scraping.ports.scraper import Scraper
from app.modules.sources import SourceRepository, SourceType, list_active_sources
from app.modules.translation import Translator, ParseError
from app.modules.listings import (
    post_listing,
    ListingRepository,
    Money,
    ContactInfo,
)


def _dedup_hash(text: str) -> str:
    norm = " ".join(text.lower().split())
    return hashlib.sha256(norm.encode()).hexdigest()[:32]


# Минимальный фильтр явного мусора: после очистки от пробелов и эмодзи
# должно остаться хотя бы 20 содержательных символов и минимум 4 буквенных слова.
_EMOJI_PUNCT_RE = re.compile(r"[\W_]+", re.UNICODE)


def _is_garbage(text: str) -> bool:
    if len(text.strip()) < 30:
        return True
    cleaned = _EMOJI_PUNCT_RE.sub(" ", text)
    words = [w for w in cleaned.split() if len(w) >= 2 and any(c.isalpha() for c in w)]
    return len(words) < 4


async def import_telegram_posts(
    *,
    scraper: Scraper,
    sources_repo: SourceRepository,
    listings_repo: ListingRepository,
    translator: Translator,
    limit_per_channel: int = 50,
) -> int:
    """Process every active Telegram source. Return total new listings posted."""
    sources = await list_active_sources(sources_repo, type=SourceType.TELEGRAM)
    total = 0

    for src in sources:
        async for raw in scraper.fetch(src.name, limit=limit_per_channel):
            # ранний скип явного мусора — экономит LLM-вызовы
            if _is_garbage(raw.text):
                continue

            existing = await listings_repo.get_by_external(src.id, raw.external_id)
            if existing is not None:
                continue

            try:
                parsed = await translator.parse_post(raw.text)
            except ParseError:
                continue

            # повторная проверка после парсинга — заголовок должен быть содержательным
            if not parsed.title or _is_garbage(parsed.title) and len(parsed.title) < 12:
                continue

            price = None
            if parsed.price_amount is not None:
                price = Money(amount=Decimal(str(parsed.price_amount)), currency=parsed.price_currency or "EUR")

            await post_listing(
                listings_repo,
                source_id=src.id,
                title=parsed.title,
                description=parsed.description,
                original_lang=parsed.original_lang,
                title_translations=parsed.title_translations,
                price=price,
                city=parsed.city,
                contact=ContactInfo(
                    telegram=parsed.contact_telegram,
                    phone=parsed.contact_phone,
                ),
                external_id=raw.external_id,
                external_url=raw.source_url,
                posted_at=raw.posted_at,
                dedup_hash=_dedup_hash(parsed.description),
                image_urls=raw.image_urls,
            )
            total += 1

        await sources_repo.mark_scraped(src.id)

    return total
