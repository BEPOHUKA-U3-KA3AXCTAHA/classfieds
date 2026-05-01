"""Cross-cutting deps: session, language. Used by every route."""
from typing import AsyncIterator
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.infra.config import get_settings
from app.infra.db import SessionLocal


async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session


def get_lang(request: Request) -> str:
    return getattr(request.state, "lang", get_settings().default_lang)
