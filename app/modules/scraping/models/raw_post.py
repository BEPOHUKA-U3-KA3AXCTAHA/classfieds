from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawPost:
    """Сырой пост из внешнего источника (Telegram, FB, OLX). Source-agnostic — адаптеры нормализуют свои ленты в эту форму."""
    external_id: str
    text: str
    posted_at: datetime
    image_urls: list[str] = field(default_factory=list)
    source_url: str | None = None


class ScrapeError(Exception):
    pass
