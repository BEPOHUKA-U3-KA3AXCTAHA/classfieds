"""SQLAdmin instance — registers ORM views from all modules."""
from fastapi import FastAPI
from sqladmin import Admin, ModelView
from sqlalchemy.ext.asyncio import AsyncEngine

from app.modules.listings.adapters.orm import ListingORM, ListingImageORM
from app.modules.catalog.adapters.orm import CategoryORM
from app.modules.sources.adapters.orm import SourceORM
from app.modules.users.adapters.orm import UserORM


class ListingAdmin(ModelView, model=ListingORM):
    column_list = [
        ListingORM.id, ListingORM.title, ListingORM.price_amount, ListingORM.price_currency,
        ListingORM.city, ListingORM.status, ListingORM.source_id, ListingORM.imported_at,
    ]
    column_searchable_list = [ListingORM.title, ListingORM.city]
    column_sortable_list = [ListingORM.id, ListingORM.imported_at, ListingORM.price_amount]


class ListingImageAdmin(ModelView, model=ListingImageORM):
    column_list = [ListingImageORM.id, ListingImageORM.listing_id, ListingImageORM.url, ListingImageORM.position]


class CategoryAdmin(ModelView, model=CategoryORM):
    column_list = [CategoryORM.id, CategoryORM.slug, CategoryORM.name_me, CategoryORM.name_ru, CategoryORM.name_en, CategoryORM.position]
    column_searchable_list = [CategoryORM.slug, CategoryORM.name_me]


class SourceAdmin(ModelView, model=SourceORM):
    column_list = [SourceORM.id, SourceORM.type, SourceORM.name, SourceORM.is_active, SourceORM.last_scraped_at]
    column_searchable_list = [SourceORM.name]


class UserAdmin(ModelView, model=UserORM):
    column_list = [UserORM.id, UserORM.email, UserORM.full_name, UserORM.is_admin, UserORM.is_active, UserORM.created_at]
    column_searchable_list = [UserORM.email, UserORM.full_name]


def setup_admin(app: FastAPI, engine: AsyncEngine) -> Admin:
    admin = Admin(app, engine, title="Oglasi.me admin")
    for view in (ListingAdmin, ListingImageAdmin, SourceAdmin, CategoryAdmin, UserAdmin):
        admin.add_view(view)
    return admin
