from typing import Protocol
from app.modules.translation.models import ParsedListing


class Translator(Protocol):
    """Driven port: parse a raw post and translate text between languages.

    Implemented by adapters that talk to an LLM (Anthropic) or a translation API.
    """

    async def parse_post(self, raw_text: str) -> ParsedListing: ...

    async def translate_text(self, text: str, src_lang: str, dst_lang: str) -> str: ...
