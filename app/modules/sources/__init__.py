"""Sources module: registry of where listings come from (telegram channels, FB groups, OLX, ...).

Pure registry — actual scraping lives in `modules/scraping/`.
"""
from app.modules.sources.models import Source, SourceType, SourceNotFound
from app.modules.sources.ports.repository import SourceRepository
from app.modules.sources.services.list_active import list_active_sources
from app.modules.sources.services.register_source import register_source

__all__ = [
    "Source",
    "SourceType",
    "SourceNotFound",
    "SourceRepository",
    "list_active_sources",
    "register_source",
]
