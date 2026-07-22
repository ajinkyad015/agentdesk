from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.auth.password import (
    hash_password,
    needs_rehash,
    verify_password,
)
from app.models.user import User
from app.repositories.user import UserRepository
from app.schemas.user import UserCreate

from app.auth.jwt import (
    create_access_token,
    create_refresh_token,
    verify_refresh_token,
)

from app.schemas.auth import TokenResponse
from app.auth.models import AuthenticationResult
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


    def _create_authentication_result(
        self,
        user: User,
    ) -> AuthenticationResult:
        """
        Create a complete authentication result for a user.
        """

        return AuthenticationResult(
            user=user,
            access_token=create_access_token(user.id),
            refresh_token=create_refresh_token(user.id),
        )


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
    ) -> AuthenticationResult:
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

        return self._create_authentication_result(user)


    async def refresh(
        self,
        refresh_token: str,
    ) -> TokenResponse:
        """
        Refresh an access token using a valid refresh token.
        """

        user_id = verify_refresh_token(refresh_token)

        user = await self.users.get(user_id)

        if user is None:
            raise InvalidCredentialsError()

        if not user.is_active:
            raise InactiveUserError()

        result = self._create_authentication_result(user)

        return TokenResponse(
            access_token=result.access_token,
            refresh_token=result.refresh_token,
        )