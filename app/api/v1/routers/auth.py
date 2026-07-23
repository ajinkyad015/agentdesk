from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import AuthServiceDep
from app.schemas.user import UserRegisterRequest, UserRegisterResponse

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


@router.post(
    "/register",
    response_model=UserRegisterResponse,
    status_code=status.HTTP_201_CREATED,
)
async def register(
    payload: UserRegisterRequest,
    service: AuthServiceDep,
) -> UserRegisterResponse:
    """
    Register a user and receive an API Key (shown once).
    """
    user, raw_key = await service.register(display_name=payload.display_name)
    return UserRegisterResponse(
        api_key=raw_key,
        user_id=user.id,
    )