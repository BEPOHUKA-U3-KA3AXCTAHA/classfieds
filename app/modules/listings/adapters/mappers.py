from decimal import Decimal
from app.modules.listings.models import Listing, ListingImage, Money, ContactInfo
from app.modules.listings.adapters.orm import ListingORM, ListingImageORM


def image_to_entity(orm: ListingImageORM) -> ListingImage:
    return ListingImage(
        id=orm.id,
        url=orm.url,
        original_url=orm.original_url,
        position=orm.position,
        phash=orm.phash,
    )


def image_to_orm(entity: ListingImage) -> ListingImageORM:
    return ListingImageORM(
        id=entity.id,
        url=entity.url,
        original_url=entity.original_url,
        position=entity.position,
        phash=entity.phash,
    )


def to_entity(orm: ListingORM) -> Listing:
    price = None
    if orm.price_amount is not None:
        price = Money(amount=orm.price_amount, currency=orm.price_currency or "EUR")
    return Listing(
        id=orm.id,
        slug=orm.slug,
        source_id=orm.source_id,
        external_id=orm.external_id,
        external_url=orm.external_url,
        author_user_id=orm.author_user_id,
        title=orm.title,
        title_translations=dict(orm.title_translations or {}),
        description=orm.description,
        description_translations=dict(orm.description_translations or {}),
        original_lang=orm.original_lang,
        price=price,
        category_id=orm.category_id,
        city=orm.city,
        contact=ContactInfo(
            telegram=orm.contact_telegram,
            phone=orm.contact_phone,
            facebook=orm.contact_facebook,
        ),
        status=orm.status,
        posted_at=orm.posted_at,
        imported_at=orm.imported_at,
        expires_at=orm.expires_at,
        last_seen_at=orm.last_seen_at,
        views=orm.views,
        dedup_hash=orm.dedup_hash,
        images=[image_to_entity(img) for img in orm.images],
    )


def to_orm(entity: Listing) -> ListingORM:
    return ListingORM(
        id=entity.id,
        slug=entity.slug,
        source_id=entity.source_id,
        external_id=entity.external_id,
        external_url=entity.external_url,
        author_user_id=entity.author_user_id,
        title=entity.title,
        title_translations=entity.title_translations,
        description=entity.description,
        description_translations=entity.description_translations,
        original_lang=entity.original_lang,
        price_amount=entity.price.amount if entity.price else None,
        price_currency=entity.price.currency if entity.price else None,
        category_id=entity.category_id,
        city=entity.city,
        contact_telegram=entity.contact.telegram,
        contact_phone=entity.contact.phone,
        contact_facebook=entity.contact.facebook,
        status=entity.status,
        posted_at=entity.posted_at,
        expires_at=entity.expires_at,
        last_seen_at=entity.last_seen_at,
        views=entity.views,
        dedup_hash=entity.dedup_hash,
        images=[image_to_orm(img) for img in entity.images],
    )
