from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sources.models import Source, SourceType
from app.modules.sources.adapters.orm import SourceORM
from app.modules.sources.adapters.mappers import to_entity


class SqlaSourceRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, id: int) -> Source | None:
        row = await self._s.get(SourceORM, id)
        return to_entity(row) if row else None

    async def get_by_name(self, type: SourceType, name: str) -> Source | None:
        stmt = select(SourceORM).where(SourceORM.type == type, SourceORM.name == name)
        row = (await self._s.execute(stmt)).scalar_one_or_none()
        return to_entity(row) if row else None

    async def list_active(self, type: SourceType | None = None) -> list[Source]:
        stmt = select(SourceORM).where(SourceORM.is_active.is_(True))
        if type is not None:
            stmt = stmt.where(SourceORM.type == type)
        stmt = stmt.order_by(SourceORM.id)
        rows = (await self._s.execute(stmt)).scalars().all()
        return [to_entity(r) for r in rows]

    async def upsert(self, source: Source) -> Source:
        existing = await self.get_by_name(source.type, source.name)
        if existing is None:
            orm = SourceORM(
                type=source.type,
                name=source.name,
                url=source.url,
                is_active=source.is_active,
            )
            self._s.add(orm)
            await self._s.flush()
            return to_entity(orm)
        existing_orm = await self._s.get(SourceORM, existing.id)
        existing_orm.url = source.url or existing_orm.url
        existing_orm.is_active = source.is_active
        await self._s.flush()
        return to_entity(existing_orm)

    async def mark_scraped(self, id: int) -> None:
        await self._s.execute(
            update(SourceORM).where(SourceORM.id == id).values(last_scraped_at=datetime.now(timezone.utc))
        )
