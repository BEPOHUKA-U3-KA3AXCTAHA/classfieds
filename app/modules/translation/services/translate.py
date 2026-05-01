from app.modules.translation.ports.translator import Translator


async def translate_description(
    translator: Translator,
    text: str,
    src_lang: str,
    dst_lang: str,
) -> str:
    return await translator.translate_text(text, src_lang, dst_lang)
