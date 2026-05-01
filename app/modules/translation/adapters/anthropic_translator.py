import json
from anthropic import AsyncAnthropic

from app.modules.translation.models import ParsedListing, ParseError


PARSE_PROMPT = """You are parsing a classified listing posted in a Telegram channel about Montenegro.

Extract structured fields from the raw text below. Output ONLY valid JSON matching this schema:
{{
  "title": "short clear title in the original language (max 100 chars)",
  "description": "full cleaned description (preserve original language; strip channel signatures and ads)",
  "title_translations": {{"me": "...", "ru": "...", "en": "..."}},
  "original_lang": "me|ru|en",
  "price_amount": number or null,
  "price_currency": "EUR|USD|RUB",
  "city": "Podgorica|Budva|Kotor|Tivat|Bar|Herceg Novi|... or null",
  "category_hint": "real_estate_rent|real_estate_sale|auto|jobs|services|electronics|furniture|other",
  "contact_telegram": "username without @ or null",
  "contact_phone": "digits only or null"
}}

Rules:
- "me" = Montenegrin (latinica). Treat Serbian as Montenegrin.
- Translate the TITLE to all 3 langs. Keep place names as-is. Do NOT translate the description here.
- For price: "500e", "500€", "500 евро" all become 500 EUR.
- Strip "@channelname", "Подписаться", emoji-only lines.

Raw post:
---
{text}
---"""


TRANSLATE_PROMPT = """Translate the classified listing description below from {src} to {dst}.

Rules:
- Preserve formatting (line breaks, lists).
- Do NOT translate place names, brand names, or contact handles.
- Keep prices and units as-is.
- Output the translation only, nothing else.

Original:
{text}"""


class AnthropicTranslator:
    """Driven adapter: implements Translator port via Anthropic Claude Haiku."""

    def __init__(self, api_key: str, model: str = "claude-haiku-4-5-20251001") -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def parse_post(self, raw_text: str) -> ParsedListing:
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            messages=[{"role": "user", "content": PARSE_PROMPT.format(text=raw_text)}],
        )
        raw = msg.content[0].text.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        try:
            data = json.loads(raw.strip())
            return ParsedListing(**data)
        except (json.JSONDecodeError, TypeError) as e:
            raise ParseError(f"Could not parse LLM output: {e}\n---\n{raw}") from e

    async def translate_text(self, text: str, src_lang: str, dst_lang: str) -> str:
        if src_lang == dst_lang:
            return text
        msg = await self._client.messages.create(
            model=self._model,
            max_tokens=2048,
            messages=[{"role": "user", "content": TRANSLATE_PROMPT.format(src=src_lang, dst=dst_lang, text=text)}],
        )
        return msg.content[0].text.strip()
