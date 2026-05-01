"""Cross-module route: home page composes listings + catalog."""
from fastapi import APIRouter, Depends, Request

from app.entrypoints.http.deps.listings import listing_repo
from app.entrypoints.http.deps.catalog import category_repo
from app.entrypoints.http.templates_setup import templates
from app.modules.listings import list_recent_listings
from app.modules.catalog import list_root_categories


router = APIRouter()


@router.get("/{lang}/")
async def home(
    lang: str,
    request: Request,
    listings_r=Depends(listing_repo),
    categories_r=Depends(category_repo),
):
    listings = await list_recent_listings(listings_r, limit=24)
    categories = await list_root_categories(categories_r)
    return templates.TemplateResponse(
        "home.html",
        {"request": request, "lang": lang, "listings": listings, "categories": categories},
    )
