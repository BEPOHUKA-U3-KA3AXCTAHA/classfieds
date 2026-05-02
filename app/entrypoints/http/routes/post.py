"""Native posting: GET форма, POST обработка."""
from fastapi import APIRouter, Depends, Form, HTTPException, Request
from fastapi.responses import RedirectResponse
from pydantic import ValidationError

from app.entrypoints.http.deps.listings import listing_repo
from app.entrypoints.http.deps.catalog import category_repo
from app.entrypoints.http.deps.sources import source_repo
from app.entrypoints.http.templates_setup import templates
from app.entrypoints.http.schemas.listing import ListingCreateForm, MONTENEGRO_CITIES, CURRENCIES

from app.modules.listings import post_listing, ListingValidationError, Money, ContactInfo
from app.modules.catalog import list_root_categories
from app.modules.sources import SourceType


router = APIRouter()


@router.get("/{lang}/post")
async def post_form(
    lang: str,
    request: Request,
    cats_repo=Depends(category_repo),
):
    categories = await list_root_categories(cats_repo)
    return templates.TemplateResponse(
        "post.html",
        {
            "request": request,
            "lang": lang,
            "categories": categories,
            "cities": MONTENEGRO_CITIES,
            "currencies": CURRENCIES,
            "form_data": {},
            "errors": [],
        },
    )


@router.post("/{lang}/post")
async def post_submit(
    lang: str,
    request: Request,
    title: str = Form(...),
    description: str = Form(...),
    category_id: str = Form(""),
    city: str = Form(""),
    price_amount: str = Form(""),
    price_currency: str = Form("EUR"),
    contact_telegram: str = Form(""),
    contact_phone: str = Form(""),
    image_urls: str = Form(""),
    cats_repo=Depends(category_repo),
    src_repo=Depends(source_repo),
    listings=Depends(listing_repo),
):
    raw = {
        "title": title,
        "description": description,
        "category_id": int(category_id) if category_id.strip() else None,
        "city": city or None,
        "price_amount": price_amount or None,
        "price_currency": price_currency or "EUR",
        "contact_telegram": contact_telegram or None,
        "contact_phone": contact_phone or None,
        "image_urls": image_urls or None,
    }
    errors: list[str] = []
    form: ListingCreateForm | None = None
    try:
        form = ListingCreateForm(**raw)
    except ValidationError as e:
        errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]

    if errors or form is None:
        categories = await list_root_categories(cats_repo)
        return templates.TemplateResponse(
            "post.html",
            {
                "request": request,
                "lang": lang,
                "categories": categories,
                "cities": MONTENEGRO_CITIES,
                "currencies": CURRENCIES,
                "form_data": raw,
                "errors": errors,
            },
            status_code=400,
        )

    # резолвим NATIVE source
    native = await src_repo.get_by_name(SourceType.NATIVE, "native")
    if native is None:
        raise HTTPException(status_code=500, detail="NATIVE source not seeded — run `python -m app.entrypoints.cli.seed sources`")

    money = Money(amount=form.price_amount, currency=form.price_currency) if form.price_amount is not None else None
    try:
        listing = await post_listing(
            listings,
            source_id=native.id,
            title=form.title,
            description=form.description,
            original_lang=lang,
            title_translations={lang: form.title},
            price=money,
            category_id=form.category_id,
            city=form.city,
            contact=ContactInfo(telegram=form.contact_telegram, phone=form.contact_phone),
            image_urls=form.parsed_image_urls(),
        )
    except ListingValidationError as e:
        errors = [str(e)]
        categories = await list_root_categories(cats_repo)
        return templates.TemplateResponse(
            "post.html",
            {"request": request, "lang": lang, "categories": categories,
             "cities": MONTENEGRO_CITIES, "currencies": CURRENCIES,
             "form_data": raw, "errors": errors},
            status_code=400,
        )

    # session.commit() делает get_session dep автоматически после возврата ответа
    return RedirectResponse(f"/{lang}/l/{listing.id}", status_code=303)
