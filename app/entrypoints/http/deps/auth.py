"""Auth-зависимости: достать current_user из cookie session, опционально или required."""
from fastapi import Depends, HTTPException, Request

from app.modules.users import User
from app.entrypoints.http.deps.users import user_repo


async def current_user_optional(
    request: Request,
    repo=Depends(user_repo),
) -> User | None:
    user_id = request.session.get("user_id")
    if not user_id:
        return None
    return await repo.get(int(user_id))


async def current_user(
    user: User | None = Depends(current_user_optional),
) -> User:
    if user is None:
        raise HTTPException(status_code=401, detail="login required")
    return user
