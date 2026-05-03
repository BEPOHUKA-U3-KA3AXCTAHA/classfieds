"""Home + поиск + фильтр + пагинация."""
from decimal import Decimal, InvalidOperation
from fastapi import APIRouter, Depends, Request, HTTPException

from app.entrypoints.http.deps.listings import listing_repo
from app.entrypoints.http.deps.catalog import category_repo
from app.entrypoints.http.templates_setup import templates
from app.modules.listings import search_listings, ListingFilters
from app.modules.catalog import list_root_categories


router = APIRouter()


def _parse_decimal(s: str | None) -> Decimal | None:
    if not s:
        return None
    try:
        return Decimal(s)
    except (InvalidOperation, ValueError):
        return None


def _parse_int(s: str | None) -> int | None:
    if not s:
        return None
    try:
        return int(s)
    except (TypeError, ValueError):
        return None


@router.get("/{lang}/")
async def home(
    lang: str,
    request: Request,
    listings_r=Depends(listing_repo),
    categories_r=Depends(category_repo),
):
    qs = request.query_params
    filters = ListingFilters(
        q=qs.get("q") or None,
        city=qs.get("city") or None,
        category_id=_parse_int(qs.get("category")),
        min_price=_parse_decimal(qs.get("min_price")),
        max_price=_parse_decimal(qs.get("max_price")),
    )
    page = max(1, _parse_int(qs.get("page")) or 1)

    page_data = await search_listings(listings_r, filters, page=page, per_page=24)
    categories = await list_root_categories(categories_r)
    active_category = None
    if filters.category_id is not None:
        active_category = next((c for c in categories if c.id == filters.category_id), None)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lang": lang,
            "page_data": page_data,
            "categories": categories,
            "filters": filters,
            "active_category": active_category,
        },
    )


@router.get("/{lang}/c/{slug}")
async def category_page(
    lang: str,
    slug: str,
    request: Request,
    listings_r=Depends(listing_repo),
    categories_r=Depends(category_repo),
):
    cat = await categories_r.get_by_slug(slug)
    if cat is None:
        raise HTTPException(status_code=404)

    qs = request.query_params
    page = max(1, _parse_int(qs.get("page")) or 1)
    filters = ListingFilters(
        q=qs.get("q") or None,
        city=qs.get("city") or None,
        category_id=cat.id,
        min_price=_parse_decimal(qs.get("min_price")),
        max_price=_parse_decimal(qs.get("max_price")),
    )

    page_data = await search_listings(listings_r, filters, page=page, per_page=24)
    categories = await list_root_categories(categories_r)

    return templates.TemplateResponse(
        "home.html",
        {
            "request": request,
            "lang": lang,
            "page_data": page_data,
            "categories": categories,
            "filters": filters,
            "active_category": cat,
        },
    )
