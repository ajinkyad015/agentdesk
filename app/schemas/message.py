from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.enums import MessageRole
from app.schemas.common import BaseResponse, SchemaModel


class MessageCreate(SchemaModel):
    """
    Request body for creating a user message.
    """

    content: str = Field(
        min_length=1,
        max_length=50_000,
    )


class MessageResponse(BaseResponse):
    """
    Response model for a message.
    """

    role: MessageRole
    content: str

    tool_name: str | None = None
    tool_arguments: dict[str, Any] | None = None
    tool_result: dict[str, Any] | None = None

    model: str | None = None

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class MessageListResponse(SchemaModel):
    """
    Response model for a list of messages.
    """

    items: list[MessageResponse]
    total: int