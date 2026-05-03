"""Бэкфилл категорий по эвристике для существующих листингов без category_id.

    python -m app.entrypoints.cli.recategorize          # все без категории
    python -m app.entrypoints.cli.recategorize --force  # переписать ВСЕ (включая уже с категорией)
"""
import asyncio
import sys

from sqlalchemy import select
from app.infra.db import SessionLocal
# регистрируем все ORM-модели в metadata чтобы FK резолвились
from app.modules.listings.adapters import orm as _l  # noqa: F401
from app.modules.catalog.adapters import orm as _c  # noqa: F401
from app.modules.sources.adapters import orm as _s  # noqa: F401
from app.modules.users.adapters import orm as _u  # noqa: F401

from app.modules.listings.adapters.orm import ListingORM
from app.modules.catalog.adapters.orm import CategoryORM
from app.modules.scraping.services.categorization import detect_slug


async def main(force: bool = False) -> None:
    async with SessionLocal() as session:
        cats = (await session.execute(select(CategoryORM.id, CategoryORM.slug))).all()
        slug_to_id = {c.slug: c.id for c in cats}

        stmt = select(ListingORM)
        if not force:
            stmt = stmt.where(ListingORM.category_id.is_(None))
        listings = (await session.execute(stmt)).scalars().all()

        applied = 0
        for l in listings:
            slug = detect_slug(f"{l.title}\n{l.description}")
            cid = slug_to_id.get(slug) if slug else None
            if cid is not None and l.category_id != cid:
                l.category_id = cid
                applied += 1

        await session.commit()
        print(f"  ✓ recategorised: {applied} (out of {len(listings)} candidates)")


if __name__ == "__main__":
    force = "--force" in sys.argv
    asyncio.run(main(force=force))
