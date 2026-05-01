"""Listing-specific routes (detail, translate)."""
from fastapi import APIRouter, Depends, HTTPException, Request

from app.entrypoints.http.deps.listings import listing_repo
from app.entrypoints.http.deps.translation import translator
from app.entrypoints.http.templates_setup import templates
from app.modules.listings import get_listing, ListingNotFound
from app.modules.translation import translate_description


router = APIRouter()


@router.get("/{lang}/l/{listing_id}")
async def listing_detail(
    lang: str,
    listing_id: int,
    request: Request,
    repo=Depends(listing_repo),
):
    try:
        listing = await get_listing(repo, listing_id)
    except ListingNotFound:
        raise HTTPException(status_code=404)
    return templates.TemplateResponse(
        "listing_detail.html",
        {"request": request, "lang": lang, "listing": listing},
    )


@router.get("/{lang}/l/{listing_id}/translate", response_class=None)
async def translate_listing(
    lang: str,
    listing_id: int,
    request: Request,
    repo=Depends(listing_repo),
    tr=Depends(translator),
):
    try:
        listing = await get_listing(repo, listing_id)
    except ListingNotFound:
        raise HTTPException(status_code=404)

    cached = (listing.description_translations or {}).get(lang)
    if cached:
        text = cached
    else:
        text = await translate_description(tr, listing.description, listing.original_lang or "me", lang)
        await repo.update_translations(listing_id, {lang: text})

    return templates.TemplateResponse(
        "_description.html",
        {"request": request, "lang": lang, "text": text},
    )
