from datetime import datetime
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Index, func
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class ConversationORM(Base):
    __tablename__ = "conversations"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    buyer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    seller_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    last_message_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    __table_args__ = (
        Index("ix_conversation_listing_buyer", "listing_id", "buyer_id", unique=True),
    )


class MessageORM(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True)
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id", ondelete="CASCADE"), index=True
    )
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)
    text: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
