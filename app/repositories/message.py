from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import MessageRole
from app.models.message import Message
from app.repositories.base import BaseRepository


class MessageRepository(BaseRepository[Message]):
    """
    Repository for Message database operations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Message)

    async def get_next_sequence_number(
        self,
        conversation_id: UUID,
    ) -> int:
        """
        Get the next sequence number for a conversation.
        """
        stmt = (
            select(func.coalesce(func.max(Message.sequence_number), 0))
            .where(Message.conversation_id == conversation_id)
        )
        result = await self.session.execute(stmt)
        return (result.scalar() or 0) + 1

    async def get_conversation_messages(
        self,
        conversation_id: UUID,
    ) -> list[Message]:
        """
        Return all messages in ordered sequence.
        """
        stmt = (
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.sequence_number.asc())
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def create_user_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        seq = await self.get_next_sequence_number(conversation_id)
        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.USER,
            content=content,
            sequence_number=seq,
        )

    async def create_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        seq = await self.get_next_sequence_number(conversation_id)
        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT,
            content=content,
            sequence_number=seq,
        )

    async def create_tool_message(
        self,
        conversation_id: UUID,
        tool_name: str,
        tool_call_id: str | None,
        tool_input: dict[str, Any] | None,
        tool_output: dict[str, Any] | None,
    ) -> Message:
        seq = await self.get_next_sequence_number(conversation_id)
        return await self.create(
            conversation_id=conversation_id,
            role=MessageRole.TOOL,
            content="",
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            tool_input=tool_input,
            tool_output=tool_output,
            sequence_number=seq,
        )

    async def delete_conversation_messages(
        self,
        conversation_id: UUID,
    ) -> int:
        stmt = (
            delete(Message)
            .where(Message.conversation_id == conversation_id)
        )

        result = await self.session.execute(stmt)
        return result.rowcount or 0