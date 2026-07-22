from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
)
from app.auth.password import (
    hash_password,
    needs_rehash,
    needs_rehash,
    verify_password,
)
from app.models import user
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate


class AuthService:
    """
    Handles registration and authentication.
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.users = UserRepository(session)

    async def register(
        self,
        data: UserCreate,
    ) -> User:
        """
        Register a new user.
        """

        if await self.users.email_exists(data.email):
            raise UserAlreadyExistsError()

        user = await self.users.create(
            email=data.email,
            full_name=data.full_name,
            password_hash=hash_password(data.password),
            is_active=True,
            email_verified=False,
            is_superuser=False,
        )

        await self.session.commit()

        await self.session.refresh(user)

        return user

    async def authenticate(
        self,
        *,
        email: str,
        password: str,
    ) -> tuple[User, str, str]:
        """
        Authenticate a user.

        Returns:
            (user, access_token, refresh_token)
        """

        user = await self.users.get_by_email(email)

        if user is None:
            raise InvalidCredentialsError()

        if not verify_password(
            password,
            user.password_hash,
        ):
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        # if needs_rehash(user.password_hash):
        #     user.password_hash = hash_password(password)

        await self.users.update_last_login(user)

        await self.session.commit()

        access_token = create_access_token(user.id)

        refresh_token = create_refresh_token(user.id)
        

        return (
            user,
            access_token,
            refresh_token,
        )