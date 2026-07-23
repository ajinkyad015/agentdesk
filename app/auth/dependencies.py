from __future__ import annotations

from typing import Annotated

from fastapi import Depends, HTTPException, Security, status
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import hash_api_key
from app.db.session import get_db
from app.models.user import User
from app.repositories.user import UserRepository

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)


async def get_current_user(
    api_key: Annotated[str | None, Security(api_key_header)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    """
    Authenticate user via API Key header 'X-API-Key'.
    """
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API Key. Include 'X-API-Key' header.",
        )

    hashed_key = hash_api_key(api_key)
    user_repo = UserRepository(db)
    user = await user_repo.get_by_api_key_hash(hashed_key)

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid API Key.",
        )

    return user