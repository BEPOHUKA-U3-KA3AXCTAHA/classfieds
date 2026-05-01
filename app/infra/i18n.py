import json
from pathlib import Path
from functools import lru_cache

from app.infra.config import get_settings


LOCALE_DIR = Path(__file__).parent / "locale"


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
