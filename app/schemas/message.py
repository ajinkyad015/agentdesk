from __future__ import annotations

from typing import Any
from uuid import UUID

from pydantic import Field

from app.models.enums import MessageRole
from app.schemas.common import SchemaModel, UUIDSchema, TimestampSchema


class MessageCreate(SchemaModel):
    """
    Request body for sending a message.
    """

    content: str = Field(
        min_length=1,
        max_length=50_000,
    )


class MessageResponse(UUIDSchema, TimestampSchema):
    """
    Response model for a message.
    """

    conversation_id: UUID
    role: MessageRole
    content: str

    tool_name: str | None = None
    tool_call_id: str | None = None
    tool_input: dict[str, Any] | None = None
    tool_output: dict[str, Any] | None = None

    sequence_number: int


class MessageListResponse(SchemaModel):
    """
    Response model for a list of messages.
    """

    items: list[MessageResponse]
    total: int