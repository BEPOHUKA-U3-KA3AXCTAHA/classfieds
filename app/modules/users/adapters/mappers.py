from app.modules.users.models import User
from app.modules.users.adapters.orm import UserORM


def to_entity(orm: UserORM) -> User:
    return User(
        id=orm.id,
        email=orm.email,
        hashed_password=orm.hashed_password,
        full_name=orm.full_name,
        phone=orm.phone,
        preferred_lang=orm.preferred_lang,
        is_active=orm.is_active,
        is_admin=orm.is_admin,
        created_at=orm.created_at,
    )


def to_orm(entity: User) -> UserORM:
    return UserORM(
        id=entity.id,
        email=entity.email,
        hashed_password=entity.hashed_password,
        full_name=entity.full_name,
        phone=entity.phone,
        preferred_lang=entity.preferred_lang,
        is_active=entity.is_active,
        is_admin=entity.is_admin,
    )
