from app.infra.config import get_settings
from app.modules.translation.ports.translator import Translator
from app.modules.translation.adapters.anthropic_translator import AnthropicTranslator


_translator: AnthropicTranslator | None = None


def translator() -> Translator:
    """Singleton — Anthropic client is cheap to keep around per process."""
    global _translator
    if _translator is None:
        _translator = AnthropicTranslator(api_key=get_settings().anthropic_api_key)
    return _translator
