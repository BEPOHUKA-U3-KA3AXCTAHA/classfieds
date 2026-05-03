from sqlalchemy import select, desc, update, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.models import Listing, ListingStatus, ListingFilters, Page
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

    async def search(
        self, filters: ListingFilters, page: int = 1, per_page: int = 24
    ) -> Page[Listing]:
        page = max(1, page)
        per_page = max(1, min(100, per_page))

        # базовый WHERE — только активные
        conds = [ListingORM.status == ListingStatus.ACTIVE]

        if filters.city:
            conds.append(ListingORM.city == filters.city)
        if filters.category_id:
            conds.append(ListingORM.category_id == filters.category_id)
        if filters.min_price is not None:
            conds.append(ListingORM.price_amount >= filters.min_price)
        if filters.max_price is not None:
            conds.append(ListingORM.price_amount <= filters.max_price)
        if filters.q:
            q_like = f"%{filters.q.strip()}%"
            conds.append(or_(
                ListingORM.title.ilike(q_like),
                ListingORM.description.ilike(q_like),
            ))

        where = and_(*conds)

        total = (await self._s.execute(
            select(func.count()).select_from(ListingORM).where(where)
        )).scalar() or 0

        stmt = (
            select(ListingORM)
            .where(where)
            .order_by(desc(ListingORM.imported_at))
            .offset((page - 1) * per_page)
            .limit(per_page)
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return Page(
            items=[to_entity(r) for r in rows],
            page=page,
            per_page=per_page,
            total=int(total),
        )
