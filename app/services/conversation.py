from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.schemas.conversation import ConversationUpdate
from app.services.exceptions import ConversationNotFoundError


class ConversationService:
    """
    Business logic for conversations and messages.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.conversations = ConversationRepository(session)
        self.messages = MessageRepository(session)

    async def create_conversation(
        self,
        *,
        user_id: UUID,
        title: str = "New Conversation",
    ) -> Conversation:
        conversation = await self.conversations.create(
            user_id=user_id,
            title=title,
        )
        await self.session.commit()
        await self.session.refresh(conversation)
        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation:
        conversation = await self.conversations.get_user_conversation(
            conversation_id,
            user_id,
        )
        if conversation is None:
            raise ConversationNotFoundError()
        return conversation

    async def list_conversations(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        return await self.conversations.get_user_conversations(
            user_id,
            offset=offset,
            limit=limit,
        )

    async def update_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        data: ConversationUpdate,
    ) -> Conversation:
        conversation = await self.get_conversation(conversation_id, user_id)
        updated = await self.conversations.update(
            conversation,
            **data.model_dump(exclude_unset=True),
        )
        await self.session.commit()
        await self.session.refresh(updated)
        return updated

    async def delete_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
    ) -> None:
        conversation = await self.get_conversation(conversation_id, user_id)
        await self.conversations.delete(conversation)
        await self.session.commit()

    async def get_messages(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> list[Message]:
        await self.get_conversation(conversation_id, user_id)
        return await self.messages.get_conversation_messages(conversation_id)

    async def add_user_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        msg = await self.messages.create_user_message(conversation_id, content)
        await self.session.flush()
        return msg

    async def add_assistant_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        msg = await self.messages.create_assistant_message(conversation_id, content)
        await self.session.flush()
        return msg

    async def add_tool_message(
        self,
        conversation_id: UUID,
        tool_name: str,
        tool_call_id: str | None,
        tool_input: dict[str, Any] | None,
        tool_output: dict[str, Any] | None,
    ) -> Message:
        msg = await self.messages.create_tool_message(
            conversation_id=conversation_id,
            tool_name=tool_name,
            tool_call_id=tool_call_id,
            tool_input=tool_input,
            tool_output=tool_output,
        )
        await self.session.flush()
        return msg