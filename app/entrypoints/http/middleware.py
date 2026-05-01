from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from app.infra.config import get_settings
from app.infra.i18n import resolve_lang


class LanguageMiddleware(BaseHTTPMiddleware):
    """Resolve language from URL prefix; expose as request.state.lang.

    Bare '/' redirects to the user's preferred language (Accept-Language) or default.
    """

    async def dispatch(self, request: Request, call_next):
        settings = get_settings()
        path = request.url.path

        # ignore non-page paths (admin, static, api etc.)
        skip_prefixes = ("/admin", "/static", "/_", "/favicon")
        if any(path.startswith(p) for p in skip_prefixes):
            request.state.lang = settings.default_lang
            return await call_next(request)

        if path in ("/", ""):
            lang = resolve_lang(None, request.headers.get("accept-language"))
            return RedirectResponse(url=f"/{lang}/", status_code=302)

        first = path.split("/", 2)[1] if len(path) > 1 else ""
        request.state.lang = first if first in settings.langs else settings.default_lang
        return await call_next(request)
