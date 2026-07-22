from __future__ import annotations

from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    status,
)
from fastapi.security import OAuth2PasswordRequestForm

from app.api.deps import (
    AuthServiceDep,
    CurrentActiveUser,
)
from app.auth.exceptions import (
    InactiveUserError,
    InvalidCredentialsError,
    UserAlreadyExistsError,
)
from app.schemas.user import (
    RefreshTokenRequest,
    TokenResponse,
    UserCreate,
    UserResponse,
)

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserCreate,
    service: AuthServiceDep,
):
    try:
        user = await service.register(payload)

    except UserAlreadyExistsError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered",
        )

    return user


@router.post(
    "/login",
    response_model=TokenResponse,
)
async def login(
    service: AuthServiceDep,
    form: OAuth2PasswordRequestForm = Depends(),
):
    try:
        result = await service.authenticate(
            email=form.username,
            password=form.password,
        )
    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={
                "WWW-Authenticate": "Bearer",
            },
        )

    except InactiveUserError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive account",
        )

    return TokenResponse(
        access_token=result.access_token,
        refresh_token=result.refresh_token,
    )


@router.post(
    "/refresh",
    response_model=TokenResponse,
)
async def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthServiceDep,
):
    return await service.refresh(payload.refresh_token)


@router.get(
    "/me",
    response_model=UserResponse,
)
async def me(
    current_user: CurrentActiveUser,
):
    return current_user