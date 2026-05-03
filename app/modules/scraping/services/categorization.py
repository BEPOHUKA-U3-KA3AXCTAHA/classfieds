"""Эвристическая категоризация: текст объявления → category_slug → category_id.

Используется и stub-translator'ом (когда нет LLM), и import_telegram_posts
для конвертации `parsed.category_hint` (строка от LLM) в id из catalog.
"""
import re
from typing import Iterable

# слаг категории → паттерны (русский / черногорский / английский ключевые слова)
_PATTERNS: list[tuple[str, list[str]]] = [
    ("real_estate", [
        r"\bаренд\w*\b", r"\bсдаю\b", r"\bснима\w*\b", r"\bстуди\w*\b",
        r"\bкварти\w*\b", r"\bапартамент\w*\b", r"\bкомнат\w*\b", r"\bдом\b",
        r"\biznajm\w*\b", r"\bstan\b", r"\bkuc\w*\b", r"\bplac\b", r"\bvila\b",
        r"\bnekretnin\w*\b", r"\brent\w*\b", r"\bapartment\b", r"\bhouse\b",
    ]),
    ("auto", [
        r"\bавто\b", r"\bмашин\w*\b", r"\bпрод(ам|аю)\s*(машин|авто)\w*",
        r"\bbmw\b", r"\baudi\b", r"\bvolkswagen\b", r"\bvw\b", r"\bmerced\w*\b",
        r"\btoyota\b", r"\bford\b", r"\bopel\b", r"\bpeugeot\b", r"\brenault\b",
        r"\bskoda\b", r"\bfiat\b", r"\bhonda\b", r"\bnissan\b", r"\bкаб?риолет\b",
        r"\bmotorbike\b", r"\bauto\b",
    ]),
    ("jobs", [
        r"\bработ\w*\b", r"\bтребу\w*\b", r"\bвакан\w*\b", r"\bищем\b",
        r"\bposao\b", r"\btrazi(mo|m)\b", r"\bjob\b", r"\bhiring\b", r"\bwork\b",
        r"\bofficiant\w*\b", r"\bводитель\b", r"\bdriver\b",
    ]),
    ("electronics", [
        r"\biphone\b", r"\bipad\b", r"\bmacbook\b", r"\bmac\s*book\b",
        r"\bsamsung\b", r"\bxiaomi\b", r"\bps[\s-]?[45]\b", r"\bnintendo\b",
        r"\bноутбук\w*\b", r"\bкомпьютер\w*\b", r"\bтелефон\w*\b", r"\bсмартфон\w*\b",
        r"\bтелевизор\w*\b", r"\blaptop\b", r"\bphone\b", r"\btv\b",
    ]),
    ("furniture", [
        r"\bдиван\w*\b", r"\bстол\b", r"\bстул\w*\b", r"\bкровать\b", r"\bшкаф\b",
        r"\bмебель\b", r"\btrpezarij\w*\b", r"\bnam(j|i)esta\w*\b", r"\bsto\b",
        r"\bstolic\w*\b", r"\bsofa\b", r"\bbed\b", r"\bfurniture\b",
    ]),
    ("services", [
        r"\bуслуг\w*\b", r"\bперевоз\w*\b", r"\bурок\w*\b", r"\bрепетит\w*\b",
        r"\bусл(уг)?и\b", r"\bremont\w*\b", r"\busluga\b", r"\bservice\b",
    ]),
    ("kids", [
        r"\bдетск\w*\b", r"\bребен\w*\b", r"\bколяск\w*\b", r"\bautolulk\w*\b",
        r"\bdjec\w*\b", r"\bkid\b", r"\bkids\b", r"\bbab(y|ies)\b", r"\bstroller\b",
    ]),
    ("clothing", [
        r"\bкуртк\w*\b", r"\bобув\w*\b", r"\bкроссов\w*\b", r"\bодежд\w*\b",
        r"\bодеж\w*\b", r"\bjakn\w*\b", r"\bodjec\w*\b", r"\bjacket\b", r"\bshoes\b",
    ]),
]

# слаги пинков от LLM-парсера (parsed.category_hint) к нашим slug'ам
_HINT_TO_SLUG = {
    "real_estate_rent": "real_estate",
    "real_estate_sale": "real_estate",
    "real_estate": "real_estate",
    "rent": "real_estate",
    "auto": "auto",
    "vehicles": "auto",
    "jobs": "jobs",
    "work": "jobs",
    "services": "services",
    "electronics": "electronics",
    "furniture": "furniture",
    "kids": "kids",
    "children": "kids",
    "clothing": "clothing",
    "other": "other",
}


def detect_slug(text: str) -> str | None:
    """Эвристика: смотрим на ключевые слова в тексте, возвращаем slug категории."""
    if not text:
        return None
    text_low = text.lower()
    for slug, patterns in _PATTERNS:
        for pat in patterns:
            if re.search(pat, text_low, re.UNICODE):
                return slug
    return None


def hint_to_slug(hint: str | None) -> str | None:
    """Нормализуем hint от LLM в наш slug."""
    if not hint:
        return None
    return _HINT_TO_SLUG.get(hint.lower().strip())


def resolve_category(slug: str | None, slug_to_id: dict[str, int]) -> int | None:
    """Slug → id из подготовленной мапы. None → None."""
    if not slug:
        return None
    return slug_to_id.get(slug)
