from dataclasses import dataclass


@dataclass
class ParsedListing:
    """Результат LLM-парсинга сырого поста в структурированные поля."""
    title: str
    description: str
    title_translations: dict[str, str]      # {"me": "...", "ru": "...", "en": "..."}
    original_lang: str
    price_amount: float | None = None
    price_currency: str | None = "EUR"
    city: str | None = None
    category_hint: str | None = None
    contact_telegram: str | None = None
    contact_phone: str | None = None


class TranslationError(Exception):
    pass


class ParseError(TranslationError):
    pass
