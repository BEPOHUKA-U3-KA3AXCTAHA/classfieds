from app.modules.catalog.models import Category
from app.modules.catalog.ports.repository import CategoryRepository


async def list_root_categories(repo: CategoryRepository) -> list[Category]:
    return await repo.list_roots()
