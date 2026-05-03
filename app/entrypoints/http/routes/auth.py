"""Auth-роуты: register / login / logout."""
from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from app.entrypoints.http.deps.users import user_repo
from app.entrypoints.http.templates_setup import templates
from app.modules.users import register_user, authenticate, EmailAlreadyTaken, UserNotFound


router = APIRouter()


@router.get("/{lang}/register")
async def register_form(lang: str, request: Request):
    return templates.TemplateResponse(
        "auth_register.html",
        {"request": request, "lang": lang, "form_data": {}, "errors": []},
    )


@router.post("/{lang}/register")
async def register_submit(
    lang: str,
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    full_name: str = Form(""),
    repo=Depends(user_repo),
):
    errors: list[str] = []
    if len(password) < 6:
        errors.append("password: минимум 6 символов")
    if "@" not in email:
        errors.append("email: некорректный")
    if errors:
        return templates.TemplateResponse(
            "auth_register.html",
            {"request": request, "lang": lang,
             "form_data": {"email": email, "full_name": full_name}, "errors": errors},
            status_code=400,
        )
    try:
        user = await register_user(repo, email=email, password=password,
                                    full_name=full_name or None, preferred_lang=lang)
    except EmailAlreadyTaken:
        return templates.TemplateResponse(
            "auth_register.html",
            {"request": request, "lang": lang,
             "form_data": {"email": email, "full_name": full_name},
             "errors": ["email уже занят"]},
            status_code=400,
        )
    request.session["user_id"] = user.id
    return RedirectResponse(f"/{lang}/", status_code=303)


@router.get("/{lang}/login")
async def login_form(lang: str, request: Request):
    return templates.TemplateResponse(
        "auth_login.html",
        {"request": request, "lang": lang, "form_data": {}, "errors": []},
    )


@router.post("/{lang}/login")
async def login_submit(
    lang: str,
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    repo=Depends(user_repo),
):
    try:
        user = await authenticate(repo, email, password)
    except UserNotFound:
        return templates.TemplateResponse(
            "auth_login.html",
            {"request": request, "lang": lang, "form_data": {"email": email},
             "errors": ["неверный email или пароль"]},
            status_code=400,
        )
    request.session["user_id"] = user.id
    next_url = request.query_params.get("next") or f"/{lang}/"
    return RedirectResponse(next_url, status_code=303)


@router.post("/{lang}/logout")
async def logout(lang: str, request: Request):
    request.session.pop("user_id", None)
    return RedirectResponse(f"/{lang}/", status_code=303)
