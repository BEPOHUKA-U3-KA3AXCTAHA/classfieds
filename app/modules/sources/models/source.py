"""Всё про источник: entity + тип + ошибки."""
import enum
from dataclasses import dataclass
from datetime import datetime


class SourceType(str, enum.Enum):
    NATIVE = "native"
    TELEGRAM = "telegram"
    FACEBOOK = "facebook"
    OLX = "olx"
    MOJKVADRAT = "mojkvadrat"


@dataclass
class Source:
    id: int | None
    type: SourceType
    name: str                            # для telegram = username канала (без @)
    url: str | None = None
    is_active: bool = True
    last_scraped_at: datetime | None = None


class SourceNotFound(Exception):
    pass
