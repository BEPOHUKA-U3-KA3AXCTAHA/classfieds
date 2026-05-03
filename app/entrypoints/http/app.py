from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from starlette.middleware.sessions import SessionMiddleware

from app.infra.config import get_settings
from app.infra.db import engine, Base
from app.infra.i18n import configure_locale
# Importing every module's orm registers its tables on Base.metadata.
from app.modules.listings.adapters import orm as _listings_orm  # noqa: F401
from app.modules.catalog.adapters import orm as _catalog_orm  # noqa: F401
from app.modules.sources.adapters import orm as _sources_orm  # noqa: F401
from app.modules.users.adapters import orm as _users_orm  # noqa: F401
from app.modules.messaging.adapters import orm as _messaging_orm  # noqa: F401

from app.entrypoints.http.middleware import LanguageMiddleware
from app.entrypoints.http.admin import setup_admin
from app.entrypoints.http.routes import home as home_routes
from app.entrypoints.http.routes import listings as listings_routes
from app.entrypoints.http.routes import post as post_routes
from app.entrypoints.http.routes import auth as auth_routes
from app.entrypoints.http.routes import chat as chat_routes


@asynccontextmanager
async def _lifespan(app: FastAPI):
    # Dev convenience: create tables. In prod we use Alembic migrations instead.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    await engine.dispose()


def create_app() -> FastAPI:
    settings = get_settings()
    # инициализация инфры: подсунуть путь к UI-локали (HTTP-слой её и владеет)
    configure_locale(Path(__file__).parent / "locale")

    app = FastAPI(title="Oglasi.me", debug=settings.debug, lifespan=_lifespan)

    # SessionMiddleware ДО LanguageMiddleware — middleware применяются reverse,
    # т.е. сессия будет внешним слоем (раскрывается раньше при request).
    app.add_middleware(SessionMiddleware, secret_key=settings.secret_key, max_age=60 * 60 * 24 * 30)
    app.add_middleware(LanguageMiddleware)

    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True)
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    # медиа — загруженные пользователями картинки
    from pathlib import Path as _P
    media_dir = _P(settings.media_dir).resolve()
    media_dir.mkdir(parents=True, exist_ok=True)
    app.mount(settings.media_url_prefix, StaticFiles(directory=str(media_dir)), name="media")

    app.include_router(home_routes.router)
    app.include_router(listings_routes.router)
    app.include_router(post_routes.router)
    app.include_router(auth_routes.router)
    app.include_router(chat_routes.router)
    setup_admin(app, engine)

    return app
