from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(
        self,
        email: str,
    ) -> User | None:
        stmt = (
            select(User)
            .where(User.email == email)
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def email_exists(
        self,
        email: str,
    ) -> bool:
        return await self.get_by_email(email) is not None

    async def get_active_by_email(
        self,
        email: str,
    ) -> User | None:
        stmt = (
            select(User)
            .where(
                User.email == email,
                User.is_active.is_(True),
            )
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def update_last_login(
        self,
        user: User,
    ) -> None:
        user.mark_login()

        await self.session.flush()