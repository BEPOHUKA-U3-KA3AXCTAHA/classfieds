from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.catalog.ports.repository import CategoryRepository
from app.modules.catalog.adapters.sqla_repository import SqlaCategoryRepository
from app.entrypoints.http.deps.core import get_session


def category_repo(session: AsyncSession = Depends(get_session)) -> CategoryRepository:
    return SqlaCategoryRepository(session)
