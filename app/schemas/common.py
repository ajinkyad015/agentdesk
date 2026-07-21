from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict
from typing import Generic, TypeVar

T = TypeVar("T")


class SchemaModel(BaseModel):
    """
    Base class for all API schemas.
    """

    model_config = ConfigDict(
        from_attributes=True,
        populate_by_name=True,
        extra="forbid",
        str_strip_whitespace=True,
    )


class TimestampSchema(SchemaModel):
    """
    Common timestamp fields.
    """

    created_at: datetime
    updated_at: datetime


class UUIDSchema(SchemaModel):
    """
    Common UUID identifier.
    """

    id: UUID


class BaseResponse(UUIDSchema, TimestampSchema):
    """
    Base response model inherited by most API response schemas.
    """

    pass

class Page(BaseModel):
    items: list[T]
    total: int
    limit: int
    offset: int