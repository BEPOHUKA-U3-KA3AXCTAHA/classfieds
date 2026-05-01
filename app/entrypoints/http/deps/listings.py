from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.listings.ports.repository import ListingRepository
from app.modules.listings.adapters.sqla_repository import SqlaListingRepository
from app.entrypoints.http.deps.core import get_session


def listing_repo(session: AsyncSession = Depends(get_session)) -> ListingRepository:
    return SqlaListingRepository(session)
