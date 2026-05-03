"""Поиск + фильтры + пагинация для листингов.

Эти типы — границу домена, доступны через `from app.modules.listings import ListingFilters, Page`.
"""
from dataclasses import dataclass, field
from decimal import Decimal
from typing import Generic, TypeVar


@dataclass
class ListingFilters:
    q: str | None = None                   # подстрока в title/description
    city: str | None = None
    category_id: int | None = None
    min_price: Decimal | None = None
    max_price: Decimal | None = None


T = TypeVar("T")


@dataclass
class Page(Generic[T]):
    items: list[T] = field(default_factory=list)
    page: int = 1
    per_page: int = 24
    total: int = 0

    @property
    def total_pages(self) -> int:
        if self.per_page <= 0:
            return 1
        return max(1, (self.total + self.per_page - 1) // self.per_page)

    @property
    def has_prev(self) -> bool:
        return self.page > 1

    @property
    def has_next(self) -> bool:
        return self.page < self.total_pages
