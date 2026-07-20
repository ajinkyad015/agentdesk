from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, select

from app.models.enums import MessageRole
from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message-specific database operations.
    """

    def __init__(self, session):
        super().__init__(session, Message)

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
    ) -> list[Message]:
        """
        Return all messages in chronological order.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.asc())
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def create_user_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        """
        Create a user message.
        """
        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
        )

    async def create_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
        *,
        model: str | None = None,
        prompt_tokens: int | None = None,
        completion_tokens: int | None = None,
        total_tokens: int | None = None,
    ) -> Message:
        """
        Create an assistant response.
        """
        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

    async def create_tool_message(
        self,
        conversation_id: UUID,
        tool_name: str,
        tool_arguments: dict[str, Any],
        tool_result: dict[str, Any],
    ) -> Message:
        """
        Store a tool execution.
        """
        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.TOOL,
            content="",
            tool_name=tool_name,
            tool_arguments=tool_arguments,
            tool_result=tool_result,
        )

    async def get_last_message(
        self,
        conversation_id: UUID,
    ) -> Message | None:
        """
        Return the newest message in a conversation.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(1)
        )

        result = await self.session.execute(stmt)

        return result.scalar_one_or_none()

    async def delete_conversation_messages(
        self,
        conversation_id: UUID,
    ) -> int:
        """
        Delete every message in a conversation.
        """
        stmt = (
            delete(Message)
            .where(Message.conversation_id == conversation_id)
        )

        result = await self.session.execute(stmt)

        return result.rowcount or 0
        