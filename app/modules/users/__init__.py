"""Users module: identity, profile, preferences. Auth flows live here when added."""
from app.modules.users.models import User, UserNotFound, EmailAlreadyTaken
from app.modules.users.ports.repository import UserRepository

__all__ = ["User", "UserNotFound", "EmailAlreadyTaken", "UserRepository"]
