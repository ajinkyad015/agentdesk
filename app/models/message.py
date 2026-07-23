from __future__ import annotations

from typing import Any, TYPE_CHECKING
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, Index, Integer, JSON, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.enums import MessageRole

if TYPE_CHECKING:
    from app.models.conversation import Conversation

JSONType = JSON().with_variant(JSONB(), "postgresql")


class Message(BaseModel):
    """
    A single message within a conversation.
    """

    __tablename__ = "messages"
    __table_args__ = (
        Index("ix_messages_conversation_id_sequence_number", "conversation_id", "sequence_number"),
    )

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
        default="",
    )

    tool_name: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tool_call_id: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )

    tool_input: Mapped[dict[str, Any] | None] = mapped_column(
        JSONType,
        nullable=True,
    )

    tool_output: Mapped[dict[str, Any] | None] = mapped_column(
        JSONType,
        nullable=True,
    )

    sequence_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
    )

    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages",
    )