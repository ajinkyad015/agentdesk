from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import UUID

from sqlalchemy import ForeignKey, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from sqlalchemy import Enum
from app.models.enums import MessageRole

from typing import Any


if TYPE_CHECKING:
    from app.models.conversation import Conversation


class Message(BaseModel):
    """
    A single message within a conversation.
    """

    __tablename__ = "messages"

    conversation_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True),
        ForeignKey("conversations.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )


    role: Mapped[MessageRole] = mapped_column(
        Enum(MessageRole, name="message_role"),
        nullable=False,
        index=True,
    )
    content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    tool_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tool_arguments: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    tool_result: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    model: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    prompt_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    completion_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    total_tokens: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
    )
    tool_call_id: Mapped[str | None] = mapped_column(
    String(100),
    nullable=True,
    )

    tool_execution_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    tool_success: Mapped[bool | None] = mapped_column(
        nullable=True,
    )