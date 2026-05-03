"""Чат между двумя юзерами вокруг одного объявления.

Conversation — диалог между buyer (тот кто написал первый) и seller (автор объявления).
Message — отдельное сообщение в диалоге.

Один Conversation = (listing_id, buyer_id, seller_id). При повторных контактах того же
buyer'а с тем же seller'ом по тому же объявлению — переиспользуем существующий conversation.
"""
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class Conversation:
    id: int | None
    listing_id: int
    buyer_id: int                  # тот кто инициировал
    seller_id: int                 # владелец объявления (или 0 если объявление scrape — пока не поддерживаем)
    created_at: datetime | None = None
    last_message_at: datetime | None = None


@dataclass
class Message:
    id: int | None
    conversation_id: int
    sender_id: int                 # buyer_id или seller_id
    text: str
    created_at: datetime | None = None


class ConversationNotFound(Exception):
    pass


class NotAConversationParticipant(Exception):
    pass


class ListingNotMessageable(Exception):
    """Объявление scrape — нельзя написать продавцу через нашу систему (только в Telegram)."""
    pass
