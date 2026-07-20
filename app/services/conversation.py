from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository


class ConversationService:
    """
    Business logic for conversations.
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

        return conversation

    async def get_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation | None:
        return await self.conversations.get_user_conversation(
            conversation_id,
            user_id,
        )

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

    async def add_user_message(
        self,
        conversation_id: UUID,
        content: str,
    ) -> Message:
        message = await self.messages.create_user_message(
            conversation_id,
            content,
        )

        await self.session.commit()

        return message

    async def history(
        self,
        conversation_id: UUID,
    ) -> list[Message]:
        return await self.messages.get_conversation_messages(
            conversation_id
        )