from dataclasses import dataclass
from datetime import datetime


@dataclass
class User:
    id: int | None
    email: str
    hashed_password: str
    full_name: str | None = None
    phone: str | None = None
    preferred_lang: str = "me"
    is_active: bool = True
    is_admin: bool = False
    created_at: datetime | None = None


class UserNotFound(Exception):
    pass


class EmailAlreadyTaken(Exception):
    pass
