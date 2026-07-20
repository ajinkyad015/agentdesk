from __future__ import annotations

from sqlalchemy import select

from app.models.user import User
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository[User]):
    """
    Repository for User-specific database operations.
    """

    def __init__(self, session):
        super().__init__(session, User)

    async def get_by_email(self, email: str) -> User | None:
        """
        Retrieve a user by email.
        """
        stmt = select(User).where(User.email == email)

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def email_exists(self, email: str) -> bool:
        """
        Check whether an email already exists.
        """
        return await self.get_by_email(email) is not None

    async def get_active_users(
        self,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[User]:
        """
        Return only active users.
        """
        stmt = (
            select(User)
            .where(User.is_active.is_(True))
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())