from sqlalchemy import String, Integer, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column

from app.infra.db import Base


class CategoryORM(Base):
    __tablename__ = "categories"

    id: Mapped[int] = mapped_column(primary_key=True)
    parent_id: Mapped[int | None] = mapped_column(ForeignKey("categories.id"), default=None)
    slug: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    name_me: Mapped[str] = mapped_column(String(128))
    name_ru: Mapped[str] = mapped_column(String(128))
    name_en: Mapped[str] = mapped_column(String(128))
    icon: Mapped[str | None] = mapped_column(String(64), default=None)
    position: Mapped[int] = mapped_column(Integer, default=0)
