from contextlib import asynccontextmanager
from typing import AsyncIterator
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.infra.config import get_settings


settings = get_settings()

engine = create_async_engine(settings.database_url, echo=settings.debug, future=True)
SessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)


class Base(DeclarativeBase):
    """Single declarative base shared across all module ORM tables.

    Module ORM models live in `modules/<mod>/adapters/orm.py` and inherit Base.
    Importing each module's orm.py is required for `Base.metadata.create_all`
    to see the tables — done in entrypoints/http/app.py lifespan.
    """


@asynccontextmanager
async def transaction(session: AsyncSession) -> AsyncIterator[None]:
    """Lightweight unit-of-work: commit on success, rollback on error."""
    try:
        yield
        await session.commit()
    except Exception:
        await session.rollback()
        raise


async def session_factory() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        yield session
