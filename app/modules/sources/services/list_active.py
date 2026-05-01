from app.modules.sources.models import Source, SourceType
from app.modules.sources.ports.repository import SourceRepository


async def list_active_sources(
    repo: SourceRepository,
    type: SourceType | None = None,
) -> list[Source]:
    return await repo.list_active(type)
