from app.modules.listings.models import Listing, ListingNotFound
from app.modules.listings.ports.repository import ListingRepository


async def get_listing(repo: ListingRepository, id: int) -> Listing:
    listing = await repo.get(id)
    if listing is None:
        raise ListingNotFound(f"Listing #{id} not found")
    return listing
