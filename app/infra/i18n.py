import json
from pathlib import Path

from app.infra.config import get_settings


# Заглушка по-умолчанию — entrypoint должен вызвать configure_locale()
# и подсунуть реальный путь к UI-строкам.
LOCALE_DIR: Path = Path(__file__).parent / "locale"


def configure_locale(path: Path) -> None:
    """Конфигурируется один раз на старте приложения (см. entrypoints/http/app.py).

    Делает infra/i18n механизмом, а данные подсовывает HTTP-слой — он же владеет UI-строками.
    """
    global LOCALE_DIR
    LOCALE_DIR = Path(path)
    _load.cache_clear()


from functools import lru_cache


@lru_cache
def _load(lang: str) -> dict[str, str]:
    path = LOCALE_DIR / f"{lang}.json"
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def t(key: str, lang: str, **kwargs) -> str:
    value = _load(lang).get(key)
    if value is None:
        value = _load(get_settings().default_lang).get(key, key)
    if kwargs:
        try:
            value = value.format(**kwargs)
        except (KeyError, IndexError):
            pass
    return value


def resolve_lang(path_lang: str | None, accept_language: str | None) -> str:
    settings = get_settings()
    if path_lang and path_lang in settings.langs:
        return path_lang
    if accept_language:
        for chunk in accept_language.split(","):
            code = chunk.split(";")[0].strip().lower().split("-")[0]
            if code in settings.langs:
                return code
    return settings.default_lang


# ───────────── relative time helper ─────────────

from datetime import datetime, timezone

_REL_TABLES = {
    "ru": [(60, "только что"), (3600, "{n} мин назад"), (86400, "{n} ч назад"),
           (604800, "{n} дн назад"), (2592000, "{n} нед назад"), (None, "{n} мес назад")],
    "me": [(60, "upravo sad"), (3600, "prije {n} min"), (86400, "prije {n} h"),
           (604800, "prije {n} dana"), (2592000, "prije {n} nedj"), (None, "prije {n} mj")],
    "en": [(60, "just now"), (3600, "{n} min ago"), (86400, "{n} h ago"),
           (604800, "{n} d ago"), (2592000, "{n} w ago"), (None, "{n} mo ago")],
}


def time_ago(dt: datetime | None, lang: str) -> str:
    """Человеко-читаемое 'X назад'. None → пустая строка."""
    if dt is None:
        return ""
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    seconds = max(0, int((now - dt).total_seconds()))
    table = _REL_TABLES.get(lang, _REL_TABLES["en"])
    divisors = {60: 1, 3600: 60, 86400: 3600, 604800: 86400, 2592000: 604800}
    for boundary, template in table:
        if boundary is None or seconds < boundary:
            if "{n}" not in template:
                return template
            div = divisors.get(boundary, 2592000)
            n = max(1, seconds // div)
            return template.format(n=n)
    return ""
