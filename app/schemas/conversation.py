from __future__ import annotations

from pydantic import Field

from app.schemas.common import BaseResponse, SchemaModel,Page


class ConversationCreate(SchemaModel):
    """
    Request body for creating a conversation.
    """

    title: str = Field(
        default="New Conversation",
        min_length=1,
        max_length=255,
    )


class ConversationUpdate(SchemaModel):
    """
    Request body for updating a conversation.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
    )


class ConversationResponse(BaseResponse):
    """
    Response returned for a single conversation.
    """

    title: str


class ConversationListResponse(SchemaModel):
    """
    Paginated conversation list.
    """

    items: list[ConversationResponse]
    total: int