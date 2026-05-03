from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.messaging.ports.repository import MessagingRepository
from app.modules.messaging.adapters.sqla_repository import SqlaMessagingRepository
from app.entrypoints.http.deps.core import get_session


def messaging_repo(session: AsyncSession = Depends(get_session)) -> MessagingRepository:
    return SqlaMessagingRepository(session)
