from datetime import datetime, timezone
from sqlalchemy import select, desc, or_, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.messaging.models import Conversation, Message
from app.modules.messaging.adapters.orm import ConversationORM, MessageORM


def _conv_to_entity(orm: ConversationORM) -> Conversation:
    return Conversation(
        id=orm.id, listing_id=orm.listing_id,
        buyer_id=orm.buyer_id, seller_id=orm.seller_id,
        created_at=orm.created_at, last_message_at=orm.last_message_at,
    )


def _msg_to_entity(orm: MessageORM) -> Message:
    return Message(
        id=orm.id, conversation_id=orm.conversation_id,
        sender_id=orm.sender_id, text=orm.text, created_at=orm.created_at,
    )


class SqlaMessagingRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._s = session

    async def get_conversation(self, id: int) -> Conversation | None:
        row = await self._s.get(ConversationORM, id)
        return _conv_to_entity(row) if row else None

    async def find_conversation(self, listing_id: int, buyer_id: int) -> Conversation | None:
        stmt = select(ConversationORM).where(
            ConversationORM.listing_id == listing_id,
            ConversationORM.buyer_id == buyer_id,
        )
        row = (await self._s.execute(stmt)).scalar_one_or_none()
        return _conv_to_entity(row) if row else None

    async def create_conversation(self, conv: Conversation) -> Conversation:
        orm = ConversationORM(
            listing_id=conv.listing_id,
            buyer_id=conv.buyer_id,
            seller_id=conv.seller_id,
        )
        self._s.add(orm)
        await self._s.flush()
        await self._s.refresh(orm)
        return _conv_to_entity(orm)

    async def list_user_conversations(self, user_id: int) -> list[Conversation]:
        stmt = (
            select(ConversationORM)
            .where(or_(ConversationORM.buyer_id == user_id, ConversationORM.seller_id == user_id))
            .order_by(desc(ConversationORM.last_message_at), desc(ConversationORM.created_at))
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return [_conv_to_entity(r) for r in rows]

    async def add_message(self, msg: Message) -> Message:
        orm = MessageORM(
            conversation_id=msg.conversation_id,
            sender_id=msg.sender_id,
            text=msg.text,
        )
        self._s.add(orm)
        await self._s.flush()
        await self._s.refresh(orm)
        return _msg_to_entity(orm)

    async def list_messages(self, conversation_id: int) -> list[Message]:
        stmt = (
            select(MessageORM)
            .where(MessageORM.conversation_id == conversation_id)
            .order_by(MessageORM.created_at, MessageORM.id)
        )
        rows = (await self._s.execute(stmt)).scalars().all()
        return [_msg_to_entity(r) for r in rows]

    async def touch_conversation(self, conversation_id: int) -> None:
        await self._s.execute(
            update(ConversationORM)
            .where(ConversationORM.id == conversation_id)
            .values(last_message_at=datetime.now(timezone.utc))
        )
