from app.modules.listings.models import Listing
from app.modules.listings.ports.repository import ListingRepository


async def list_recent_listings(repo: ListingRepository, limit: int = 24) -> list[Listing]:
    return await repo.list_recent(limit=limit)
