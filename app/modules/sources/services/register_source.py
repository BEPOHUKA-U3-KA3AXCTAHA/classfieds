from app.modules.sources.models import Source, SourceType
from app.modules.sources.ports.repository import SourceRepository


async def register_source(
    repo: SourceRepository,
    type: SourceType,
    name: str,
    url: str | None = None,
) -> Source:
    return await repo.upsert(Source(id=None, type=type, name=name, url=url, is_active=True))
