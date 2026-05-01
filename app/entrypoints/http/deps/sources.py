from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.sources.ports.repository import SourceRepository
from app.modules.sources.adapters.sqla_repository import SqlaSourceRepository
from app.entrypoints.http.deps.core import get_session


def source_repo(session: AsyncSession = Depends(get_session)) -> SourceRepository:
    return SqlaSourceRepository(session)
