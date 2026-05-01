from app.modules.catalog.models import Category
from app.modules.catalog.adapters.orm import CategoryORM


def to_entity(orm: CategoryORM) -> Category:
    return Category(
        id=orm.id,
        parent_id=orm.parent_id,
        slug=orm.slug,
        name_me=orm.name_me,
        name_ru=orm.name_ru,
        name_en=orm.name_en,
        icon=orm.icon,
        position=orm.position,
    )


def to_orm(entity: Category) -> CategoryORM:
    return CategoryORM(
        id=entity.id,
        parent_id=entity.parent_id,
        slug=entity.slug,
        name_me=entity.name_me,
        name_ru=entity.name_ru,
        name_en=entity.name_en,
        icon=entity.icon,
        position=entity.position,
    )
