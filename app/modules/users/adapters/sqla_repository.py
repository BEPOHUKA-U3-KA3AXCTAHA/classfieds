from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.users.models import User
from app.modules.users.adapters.orm import UserORM
from app.modules.users.adapters.mappers import to_entity, to_orm


class SqlaUserRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get(self, id: int) -> User | None:
        row = await self._s.get(UserORM, id)
        return to_entity(row) if row else None

    async def get_by_email(self, email: str) -> User | None:
        stmt = select(UserORM).where(UserORM.email == email)
        row = (await self._s.execute(stmt)).scalar_one_or_none()
        return to_entity(row) if row else None

    async def add(self, user: User) -> User:
        orm = to_orm(user)
        self._s.add(orm)
        await self._s.flush()
        return to_entity(orm)
