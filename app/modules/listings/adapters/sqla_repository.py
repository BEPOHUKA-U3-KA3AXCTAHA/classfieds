from sqlalchemy import select, desc, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.models import Listing, ListingStatus
from app.modules.listings.adapters.orm import ListingORM
from app.modules.listings.adapters.mappers import to_entity, to_orm


class SqlaListingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, id: int) -> Listing | None:
        row = await self._s.get(ListingORM, id)
        return to_entity(row) if row else None

    async def list_recent(
        self, limit: int = 24, status: ListingStatus = ListingStatus.ACTIVE
    ) -> list[Listing]:
        stmt = (
            select(ListingORM)
            .where(ListingORM.status == status)
            .order_by(desc(ListingORM.imported_at))
            .limit(limit)
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return [to_entity(r) for r in rows]

    async def get_by_external(self, source_id: int, external_id: str) -> Listing | None:
        stmt = select(ListingORM).where(
            ListingORM.source_id == source_id, ListingORM.external_id == external_id
        )
        row = (await self._s.execute(stmt)).scalar_one_or_none()
        return to_entity(row) if row else None

    async def add(self, listing: Listing) -> Listing:
        orm = to_orm(listing)
        self._s.add(orm)
        await self._s.flush()
        await self._s.refresh(orm)
        return to_entity(orm)

    async def update_translations(self, id: int, descriptions: dict[str, str]) -> None:
        listing = await self._s.get(ListingORM, id)
        if listing is None:
            return
        merged = dict(listing.description_translations or {})
        merged.update(descriptions)
        listing.description_translations = merged
        await self._s.flush()
