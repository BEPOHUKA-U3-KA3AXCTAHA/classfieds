"""Catalog module: categories (and later cities) — reference data shared across modules.

Public API: import from this module, do NOT reach into submodules from outside.
"""
from app.modules.catalog.models import Category, CategoryNotFound
from app.modules.catalog.ports.repository import CategoryRepository
from app.modules.catalog.services.list_categories import list_root_categories

__all__ = ["Category", "CategoryNotFound", "CategoryRepository", "list_root_categories"]
