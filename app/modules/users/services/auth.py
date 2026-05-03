"""Auth-сервисы: регистрация, проверка пароля. bcrypt для хеширования."""
import bcrypt

from app.modules.users.models import User, EmailAlreadyTaken, UserNotFound
from app.modules.users.ports.repository import UserRepository


def _hash(plain: str) -> str:
    return bcrypt.hashpw(plain.encode(), bcrypt.gensalt()).decode()


def _verify(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode(), hashed.encode())
    except (ValueError, TypeError):
        return False


async def register_user(
    repo: UserRepository,
    *,
    email: str,
    password: str,
    full_name: str | None = None,
    preferred_lang: str = "me",
) -> User:
    email = email.strip().lower()
    if await repo.get_by_email(email):
        raise EmailAlreadyTaken(email)
    user = User(
        id=None,
        email=email,
        hashed_password=_hash(password),
        full_name=full_name,
        preferred_lang=preferred_lang,
    )
    return await repo.add(user)


async def authenticate(repo: UserRepository, email: str, password: str) -> User:
    user = await repo.get_by_email(email.strip().lower())
    if user is None or not _verify(password, user.hashed_password):
        raise UserNotFound("invalid email or password")
    return user
