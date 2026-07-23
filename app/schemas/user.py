from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import SchemaModel


class UserRegisterRequest(SchemaModel):
    """
    Request body for user registration.
    """

    display_name: str = Field(
        min_length=1,
        max_length=255,
        description="Name of the user",
    )


class UserRegisterResponse(SchemaModel):
    """
    Response returned on user registration (API key shown once).
    """

    api_key: str
    user_id: UUID


class UserResponse(SchemaModel):
    """
    Public user representation.
    """

    id: UUID
    display_name: str
    created_at: datetime