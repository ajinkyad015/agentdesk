from __future__ import annotations

from typing import Any, Literal
from uuid import UUID

from pydantic import Field

from app.schemas.common import SchemaModel
from app.schemas.message import MessageResponse


class ChatRequest(SchemaModel):
    """
    Request body for a chat completion.
    """

    conversation_id: UUID
    message: str = Field(
        min_length=1,
        max_length=50_000,
    )


class ChatResponse(SchemaModel):
    """
    Response returned after processing one chat turn.
    """

    conversation_id: UUID

    message: MessageResponse

    model: str | None = None

    prompt_tokens: int | None = None
    completion_tokens: int | None = None
    total_tokens: int | None = None


class ChatStreamChunk(SchemaModel):
    """
    Represents one streamed chunk of a chat response.
    """

    conversation_id: UUID

    delta: str = ""

    done: bool = False

    metadata: dict[str, Any] | None = None

class TextDeltaEvent(SchemaModel):
    event: Literal["text"]
    delta: str


class ToolCallEvent(SchemaModel):
    event: Literal["tool_call"]
    tool_name: str
    arguments: dict[str, Any]


class ToolResultEvent(SchemaModel):
    event: Literal["tool_result"]
    result: dict[str, Any]


class DoneEvent(SchemaModel):
    event: Literal["done"]