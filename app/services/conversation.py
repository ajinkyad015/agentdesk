from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.message import Message
from app.repositories.conversation import ConversationRepository
from app.repositories.message import MessageRepository
from app.models.conversation import Conversation
from app.schemas.conversation import ConversationUpdate
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
        await self.session.refresh(conversation)
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





    async def update_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        data: ConversationUpdate,
    ) -> Conversation:
        """
        Update a user's conversation.
        """

        conversation = await self.conversations.get_user_conversation(
            conversation_id,
            user_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        conversation = await self.conversations.update(
            conversation,
            **data.model_dump(exclude_unset=True),
        )

        await self.session.commit()

        await self.session.refresh(conversation)

        return conversation


    async def delete_conversation(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
    ) -> None:
        """
        Delete a user's conversation.
        """

        conversation = await self.conversations.get_user_conversation(
            conversation_id,
            user_id,
        )

        if conversation is None:
            raise ValueError("Conversation not found")

        await self.conversations.delete(conversation)

        await self.session.commit()


    async def add_assistant_message(
        self,
        *,
        conversation_id: UUID,
        content: str,
        model: str,
        prompt_tokens: int,
        completion_tokens: int,
        total_tokens: int,
    ) -> Message:
        message = await self.messages.create_assistant_message(
            conversation_id=conversation_id,
            content=content,
            model=model,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
        )

        await self.session.commit()

        return message