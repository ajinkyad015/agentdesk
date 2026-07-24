from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.security import generate_api_key, hash_api_key
from app.models.user import User
from app.repositories.user import UserRepository


class AuthService:
    def __init__(self, session: AsyncSession):
        self.session = session
        self.user_repo = UserRepository(session)

    async def register(
        self,
        display_name: str,
    ) -> tuple[User, str]:
        """
        Register a new user and generate a new API key.
        Returns (user, raw_api_key).
        """
        raw_key = generate_api_key()
        key_hash = hash_api_key(raw_key)

        user = await self.user_repo.create_user(
            display_name=display_name,
            api_key_hash=key_hash,
        )
        await self.session.commit()
        await self.session.refresh(user)

        return user, raw_key