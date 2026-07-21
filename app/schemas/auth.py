from __future__ import annotations

from pydantic import EmailStr, Field

from app.schemas.common import BaseResponse, SchemaModel



class UserLogin(SchemaModel):
    """
    Login request.
    """

    email: EmailStr

    password: str


class TokenResponse(SchemaModel):
    """
    JWT authentication response.
    """

    access_token: str
    refresh_token: str
    expires_in: int
    token_type: str = "bearer"

class RefreshTokenRequest(SchemaModel):
    """
    Refresh access token request.
    """

    refresh_token: str


class RefreshTokenResponse(SchemaModel):
    """
    Response after refreshing an access token.
    """

    access_token: str

    token_type: str = "bearer"


class ChangePasswordRequest(SchemaModel):
    """
    Request body for changing a password.
    """

    current_password: str

    new_password: str = Field(
        min_length=8,
        max_length=128,
    )