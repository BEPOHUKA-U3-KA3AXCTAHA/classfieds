"""Всё про объявление в одном месте: entity + статус + ошибки."""
import enum
from dataclasses import dataclass, field
from datetime import datetime

from app.modules.listings.models.money import Money
from app.modules.listings.models.contact import ContactInfo


class ListingStatus(str, enum.Enum):
    PENDING = "pending"
    ACTIVE = "active"
    HIDDEN = "hidden"
    SOLD = "sold"
    ARCHIVED = "archived"


@dataclass
class ListingImage:
    id: int | None
    url: str
    original_url: str | None = None
    position: int = 0
    phash: str | None = None


@dataclass
class Listing:
    id: int | None
    slug: str
    source_id: int                            # FK → sources.Source
    external_id: str | None                   # post id в источнике (если со скрейпа)
    external_url: str | None
    author_user_id: int | None                # FK → users.User (только для нативных постов)

    title: str
    title_translations: dict[str, str] = field(default_factory=dict)

    description: str = ""
    description_translations: dict[str, str] = field(default_factory=dict)
    original_lang: str | None = None

    price: Money | None = None
    category_id: int | None = None
    city: str | None = None
    contact: ContactInfo = field(default_factory=ContactInfo)

    status: ListingStatus = ListingStatus.ACTIVE
    posted_at: datetime | None = None
    imported_at: datetime | None = None
    expires_at: datetime | None = None
    last_seen_at: datetime | None = None

    views: int = 0
    dedup_hash: str | None = None
    images: list[ListingImage] = field(default_factory=list)

    def title_for(self, lang: str) -> str:
        return self.title_translations.get(lang) or self.title

    def description_for(self, lang: str) -> str:
        if lang == self.original_lang:
            return self.description
        return self.description_translations.get(lang) or self.description


class ListingNotFound(Exception):
    pass


class ListingValidationError(Exception):
    pass
