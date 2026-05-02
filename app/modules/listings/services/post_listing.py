from datetime import datetime, timezone
from slugify import slugify

from app.modules.listings.models import (
    Listing, ListingImage, ListingStatus, ListingValidationError, Money, ContactInfo,
)
from app.modules.listings.ports.repository import ListingRepository


async def post_listing(
    repo: ListingRepository,
    *,
    source_id: int,
    title: str,
    description: str,
    original_lang: str,
    title_translations: dict[str, str] | None = None,
    price: Money | None = None,
    category_id: int | None = None,
    city: str | None = None,
    contact: ContactInfo | None = None,
    author_user_id: int | None = None,
    external_id: str | None = None,
    external_url: str | None = None,
    posted_at: datetime | None = None,
    dedup_hash: str | None = None,
    status: ListingStatus = ListingStatus.ACTIVE,
    image_urls: list[str] | None = None,
) -> Listing:
    if not title.strip():
        raise ListingValidationError("Title is required")
    if not description.strip():
        raise ListingValidationError("Description is required")

    images = [
        ListingImage(id=None, url=url, original_url=url, position=i)
        for i, url in enumerate(image_urls or [])
    ]

    listing = Listing(
        id=None,
        slug=slugify(title)[:120] or "listing",
        source_id=source_id,
        external_id=external_id,
        external_url=external_url,
        author_user_id=author_user_id,
        title=title,
        title_translations=title_translations or {},
        description=description,
        original_lang=original_lang,
        price=price,
        category_id=category_id,
        city=city,
        contact=contact or ContactInfo(),
        status=status,
        posted_at=posted_at,
        last_seen_at=datetime.now(timezone.utc),
        dedup_hash=dedup_hash,
        images=images,
    )
    return await repo.add(listing)
