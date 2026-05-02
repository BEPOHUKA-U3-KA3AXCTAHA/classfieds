"""Помечает старые объявления как ARCHIVED.

Правила:
- ACTIVE объявление не обновлялось N дней (last_seen_at < now - N) → ARCHIVED
- N по умолчанию 30 дней; передай число днями аргументом

Использование:
    python -m app.entrypoints.cli.archive_stale         # 30 дней
    python -m app.entrypoints.cli.archive_stale 60      # 60 дней
"""
import asyncio
import sys
from datetime import datetime, timedelta, timezone

from sqlalchemy import update, and_

from app.infra.db import SessionLocal
from app.modules.listings.adapters.orm import ListingORM
from app.modules.listings.models import ListingStatus


async def main(days: int = 30) -> None:
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    async with SessionLocal() as session:
        stmt = (
            update(ListingORM)
            .where(and_(
                ListingORM.status == ListingStatus.ACTIVE,
                ListingORM.last_seen_at < cutoff,
            ))
            .values(status=ListingStatus.ARCHIVED)
        )
        result = await session.execute(stmt)
        await session.commit()
        print(f"  ✓ archived {result.rowcount} listings stale > {days}d")


if __name__ == "__main__":
    days = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    asyncio.run(main(days))
