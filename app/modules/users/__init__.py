"""Users module: identity, profile, auth."""
from app.modules.users.models import User, UserNotFound, EmailAlreadyTaken
from app.modules.users.ports.repository import UserRepository
from app.modules.users.services.auth import register_user, authenticate

__all__ = ["User", "UserNotFound", "EmailAlreadyTaken", "UserRepository", "register_user", "authenticate"]
