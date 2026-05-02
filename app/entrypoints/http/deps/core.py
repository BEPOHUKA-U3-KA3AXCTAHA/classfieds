"""Cross-cutting deps: session, language. Used by every route."""
from typing import AsyncIterator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.config import get_settings
from app.infra.db import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:
    """Auto-commit on success, rollback on exception. Чтения и пустые сессии — no-op."""
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


def get_lang(request: Request) -> str:
    return getattr(request.state, "lang", get_settings().default_lang)
