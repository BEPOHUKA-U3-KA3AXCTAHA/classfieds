"""Pydantic-схемы HTTP-границы для модуля listings.

Лежат в `entrypoints/http/schemas/` — НЕ в самом модуле listings, чтобы домен
не знал про Pydantic. Здесь — валидация формы, дальше преобразуем в чистые
доменные value objects (Money, ContactInfo) перед вызовом сервиса.
"""
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, Field, field_validator

# Список городов вынесен сюда же чтобы дроп-даун в форме был синхронен
MONTENEGRO_CITIES = [
    "Podgorica", "Budva", "Kotor", "Tivat", "Bar", "Herceg Novi",
    "Cetinje", "Ulcinj", "Niksic", "Bijelo Polje", "Berane", "Pljevlja",
]

CURRENCIES = ["EUR", "USD", "RUB"]


class ListingCreateForm(BaseModel):
    title: Annotated[str, Field(min_length=4, max_length=200)]
    description: Annotated[str, Field(min_length=20, max_length=4000)]
    category_id: int | None = None
    city: str | None = None
    price_amount: Decimal | None = None
    price_currency: str = "EUR"
    contact_telegram: str | None = None
    contact_phone: str | None = None
    image_urls: str | None = None  # многострочный textarea, по одному URL на строку

    @field_validator("city")
    @classmethod
    def _city_known(cls, v: str | None) -> str | None:
        if v is None or v == "":
            return None
        if v not in MONTENEGRO_CITIES:
            raise ValueError(f"unknown city: {v}")
        return v

    @field_validator("price_currency")
    @classmethod
    def _currency_known(cls, v: str) -> str:
        if v not in CURRENCIES:
            raise ValueError(f"currency must be one of {CURRENCIES}")
        return v

    @field_validator("contact_telegram")
    @classmethod
    def _strip_at(cls, v: str | None) -> str | None:
        if not v:
            return None
        return v.lstrip("@").strip() or None

    def parsed_image_urls(self) -> list[str]:
        if not self.image_urls:
            return []
        return [
            line.strip()
            for line in self.image_urls.splitlines()
            if line.strip().startswith("http")
        ][:8]
