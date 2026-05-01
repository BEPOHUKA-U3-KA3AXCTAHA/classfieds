from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.models import Category
from app.modules.catalog.adapters.orm import CategoryORM
from app.modules.catalog.adapters.mappers import to_entity


class SqlaCategoryRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def list_roots(self) -> list[Category]:
        stmt = select(CategoryORM).where(CategoryORM.parent_id.is_(None)).order_by(CategoryORM.position)
        rows = (await self._s.execute(stmt)).scalars().all()
        return [to_entity(r) for r in rows]

    async def get_by_slug(self, slug: str) -> Category | None:
        stmt = select(CategoryORM).where(CategoryORM.slug == slug)
        row = (await self._s.execute(stmt)).scalar_one_or_none()
        return to_entity(row) if row else None

    async def get(self, id: int) -> Category | None:
        row = await self._s.get(CategoryORM, id)
        return to_entity(row) if row else None
