from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.ports.repository import UserRepository
from app.modules.users.adapters.sqla_repository import SqlaUserRepository
from app.entrypoints.http.deps.core import get_session


def user_repo(session: AsyncSession = Depends(get_session)) -> UserRepository:
    return SqlaUserRepository(session)
