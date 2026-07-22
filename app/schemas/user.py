from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.common import BaseResponse, SchemaModel


class UserCreate(SchemaModel):
    """
    Request body for user registration.
    """

    email: EmailStr

    full_name: str = Field(
        min_length=1,
        max_length=255,
    )

    password: str = Field(
        min_length=8,
        max_length=128,
    )


class UserUpdate(SchemaModel):
    """
    Request body for updating a user profile.
    """

    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )


class UserResponse(BaseResponse):
    """
    Public user information.
    """

    email: EmailStr

    full_name: str

    is_active: bool
    email_verified: bool
