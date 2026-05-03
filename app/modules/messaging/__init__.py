"""Messaging module: внутренний чат между юзерами вокруг объявления."""
from app.modules.messaging.models import (
    Conversation, Message,
    ConversationNotFound, NotAConversationParticipant, ListingNotMessageable,
)
from app.modules.messaging.ports.repository import MessagingRepository
from app.modules.messaging.services.chat import (
    open_or_get_conversation, send_message, get_thread,
)

__all__ = [
    "Conversation", "Message",
    "ConversationNotFound", "NotAConversationParticipant", "ListingNotMessageable",
    "MessagingRepository",
    "open_or_get_conversation", "send_message", "get_thread",
]
