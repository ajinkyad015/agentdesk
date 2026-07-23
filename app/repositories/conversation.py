from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.orm import selectinload
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.repositories.base import BaseRepository


class ConversationRepository(BaseRepository[Conversation]):
    """
    Repository for Conversation database operations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Conversation)

    async def get_user_conversations(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Conversation]:
        """
        Return all conversations for a user.
        """
        stmt = (
            select(Conversation)
            .where(Conversation.user_id == user_id)
            .order_by(Conversation.updated_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_with_messages(
        self,
        conversation_id: UUID,
    ) -> Conversation | None:
        """
        Load a conversation together with all its messages.
        """
        stmt = (
            select(Conversation)
            .options(
                selectinload(Conversation.messages)
            )
            .where(Conversation.id == conversation_id)
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_user_conversation(
        self,
        conversation_id: UUID,
        user_id: UUID,
    ) -> Conversation | None:
        """
        Return a conversation only if it belongs to the user.
        """
        stmt = (
            select(Conversation)
            .where(
                Conversation.id == conversation_id,
                Conversation.user_id == user_id,
            )
        )

        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def delete_user_conversations(
        self,
        user_id: UUID,
    ) -> int:
        """
        Delete all conversations belonging to a user.
        """
        stmt = (
            delete(Conversation)
            .where(Conversation.user_id == user_id)
        )

        result = await self.session.execute(stmt)
        return result.rowcount or 0