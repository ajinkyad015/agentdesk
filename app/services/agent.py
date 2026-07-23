from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.chat import ChatResponse
from app.services.conversation import ConversationService
from app.services.llm import LLMService
from app.services.exceptions import ConversationNotFoundError
from collections.abc import AsyncIterator



class AgentService:
    """
    Orchestrates a complete AI conversation turn.

    Responsibilities:
    - Validate the conversation exists
    - Persist the user's message
    - Load conversation history
    - Call the LLM
    - Persist the assistant's response
    - Return a ChatResponse
    """

    def __init__(
        self,
        session: AsyncSession,
    ):
        self.session = session
        self.conversations = ConversationService(session)
        self.llm = LLMService()

    async def chat(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        message: str,
    ) -> ChatResponse:
        """
        Execute one complete conversation turn.
        """

        conversation = await self.conversations.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ConversationNotFoundError()

        await self.conversations.add_user_message(
            conversation_id=conversation_id,
            content=message,
        )

        history = await self.conversations.history(
            conversation_id=conversation_id,
        )

        response = await self.llm.generate(history)

        await self.conversations.add_assistant_message(
            conversation_id=conversation_id,
            content=response.content,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
        )

        return ChatResponse(
            conversation_id=conversation_id,
            message=response.content,
            model=response.model,
            prompt_tokens=response.prompt_tokens,
            completion_tokens=response.completion_tokens,
            total_tokens=response.total_tokens,
        )

    
    async def stream_chat(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        message: str,
    ) -> AsyncIterator[str]:
        """
        Execute one complete conversation turn using streaming.
        """

        conversation = await self.conversations.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )

        if conversation is None:
            raise ConversationNotFoundError()

        await self.conversations.add_user_message(
            conversation_id=conversation_id,
            content=message,
        )

        history = await self.conversations.history(
            conversation_id=conversation_id,
        )

        chunks: list[str] = []

        async for chunk in self.llm.stream(history):
            chunks.append(chunk)
            yield chunk

        content = "".join(chunks)

        await self.conversations.add_assistant_message(
            conversation_id=conversation_id,
            content=content,
            model=self.llm.model,
            prompt_tokens=0,
            completion_tokens=0,
            total_tokens=0,
        )

        await self.session.commit()