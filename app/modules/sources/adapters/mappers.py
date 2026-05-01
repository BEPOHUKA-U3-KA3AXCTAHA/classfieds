from app.modules.sources.models import Source
from app.modules.sources.adapters.orm import SourceORM


def to_entity(orm: SourceORM) -> Source:
    return Source(
        id=orm.id,
        type=orm.type,
        name=orm.name,
        url=orm.url,
        is_active=orm.is_active,
        last_scraped_at=orm.last_scraped_at,
    )


def to_orm(entity: Source) -> SourceORM:
    return SourceORM(
        id=entity.id,
        type=entity.type,
        name=entity.name,
        url=entity.url,
        is_active=entity.is_active,
        last_scraped_at=entity.last_scraped_at,
    )
