"""Chat use cases: open conversation, send message, get thread.

Кросс-модульная зависимость: listings.get_listing — чтобы узнать seller_id (author_user_id листинга).
"""
from app.modules.messaging.models import (
    Conversation, Message,
    ConversationNotFound, NotAConversationParticipant, ListingNotMessageable,
)
from app.modules.messaging.ports.repository import MessagingRepository
from app.modules.listings import get_listing, ListingRepository, ListingNotFound


async def open_or_get_conversation(
    repo: MessagingRepository,
    listings_repo: ListingRepository,
    *,
    listing_id: int,
    buyer_id: int,
) -> Conversation:
    """Ищет существующий conversation между buyer и автором listing, или создаёт новый.

    raises ListingNotFound | ListingNotMessageable
    """
    listing = await get_listing(listings_repo, listing_id)
    if listing.author_user_id is None:
        raise ListingNotMessageable("это объявление взято с внешнего источника, контакт через Telegram")

    if listing.author_user_id == buyer_id:
        # сам с собой не пишет
        raise NotAConversationParticipant("нельзя написать самому себе")

    existing = await repo.find_conversation(listing_id, buyer_id)
    if existing is not None:
        return existing

    return await repo.create_conversation(
        Conversation(id=None, listing_id=listing_id, buyer_id=buyer_id, seller_id=listing.author_user_id)
    )


async def send_message(
    repo: MessagingRepository,
    *,
    conversation_id: int,
    sender_id: int,
    text: str,
) -> Message:
    text = text.strip()
    if not text:
        raise ValueError("empty message")

    conv = await repo.get_conversation(conversation_id)
    if conv is None:
        raise ConversationNotFound(str(conversation_id))
    if sender_id not in (conv.buyer_id, conv.seller_id):
        raise NotAConversationParticipant("не участник этого диалога")

    msg = await repo.add_message(Message(
        id=None, conversation_id=conversation_id, sender_id=sender_id, text=text
    ))
    await repo.touch_conversation(conversation_id)
    return msg


async def get_thread(
    repo: MessagingRepository,
    *,
    conversation_id: int,
    user_id: int,
) -> tuple[Conversation, list[Message]]:
    conv = await repo.get_conversation(conversation_id)
    if conv is None:
        raise ConversationNotFound(str(conversation_id))
    if user_id not in (conv.buyer_id, conv.seller_id):
        raise NotAConversationParticipant("не участник этого диалога")
    messages = await repo.list_messages(conversation_id)
    return conv, messages
