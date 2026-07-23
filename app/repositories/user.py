from __future__ import annotations

from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=User)

    async def get_by_api_key_hash(
        self,
        api_key_hash: str,
    ) -> User | None:
        stmt = (
            select(User)
            .where(User.api_key_hash == api_key_hash)
            .limit(1)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_user(
        self,
        *,
        display_name: str,
        api_key_hash: str,
    ) -> User:
        user = User(
            display_name=display_name,
            api_key_hash=api_key_hash,
        )
        self.session.add(user)
        await self.session.flush()
        await self.session.refresh(user)
        return user