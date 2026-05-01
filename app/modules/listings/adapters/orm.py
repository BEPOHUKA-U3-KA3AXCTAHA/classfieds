from datetime import datetime
from decimal import Decimal
from sqlalchemy import String, Text, Integer, ForeignKey, DateTime, Enum, Numeric, JSON, func, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.infra.db import Base
from app.modules.listings.models import ListingStatus


class ListingORM(Base):
    __tablename__ = "listings"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), index=True)

    source_id: Mapped[int] = mapped_column(ForeignKey("sources.id"), index=True)
    external_id: Mapped[str | None] = mapped_column(String(255), default=None)
    external_url: Mapped[str | None] = mapped_column(String(512), default=None)

    author_user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), default=None, index=True)

    title: Mapped[str] = mapped_column(String(512))
    title_translations: Mapped[dict] = mapped_column(JSON, default=dict)

    description: Mapped[str] = mapped_column(Text, default="")
    description_translations: Mapped[dict] = mapped_column(JSON, default=dict)
    original_lang: Mapped[str | None] = mapped_column(String(8), default=None)

    price_amount: Mapped[Decimal | None] = mapped_column(Numeric(12, 2), default=None)
    price_currency: Mapped[str | None] = mapped_column(String(8), default="EUR")

    category_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), default=None, index=True)
    city: Mapped[str | None] = mapped_column(String(128), default=None, index=True)

    contact_telegram: Mapped[str | None] = mapped_column(String(128), default=None)
    contact_phone: Mapped[str | None] = mapped_column(String(64), default=None)
    contact_facebook: Mapped[str | None] = mapped_column(String(255), default=None)

    status: Mapped[ListingStatus] = mapped_column(
        Enum(ListingStatus, name="listing_status"), default=ListingStatus.ACTIVE, index=True
    )

    posted_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    imported_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    expires_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    last_seen_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    views: Mapped[int] = mapped_column(Integer, default=0)
    dedup_hash: Mapped[str | None] = mapped_column(String(64), default=None, index=True)

    images: Mapped[list["ListingImageORM"]] = relationship(
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="ListingImageORM.position",
        lazy="selectin",
    )

    __table_args__ = (
        Index("ix_listings_source_external", "source_id", "external_id", unique=True),
    )


class ListingImageORM(Base):
    __tablename__ = "listing_images"

    id: Mapped[int] = mapped_column(primary_key=True)
    listing_id: Mapped[int] = mapped_column(ForeignKey("listings.id", ondelete="CASCADE"), index=True)
    url: Mapped[str] = mapped_column(String(1024))
    original_url: Mapped[str | None] = mapped_column(String(1024), default=None)
    position: Mapped[int] = mapped_column(Integer, default=0)
    phash: Mapped[str | None] = mapped_column(String(64), default=None, index=True)

    listing: Mapped[ListingORM] = relationship(back_populates="images")
