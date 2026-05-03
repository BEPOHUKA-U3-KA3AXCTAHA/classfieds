from app.modules.listings.models import ListingFilters, Listing, Page
from app.modules.listings.ports.repository import ListingRepository


async def search_listings(
    repo: ListingRepository,
    filters: ListingFilters,
    page: int = 1,
    per_page: int = 24,
) -> Page[Listing]:
    return await repo.search(filters=filters, page=page, per_page=per_page)
