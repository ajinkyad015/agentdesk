from __future__ import annotations

import json
from typing import AsyncIterator
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMClient
from app.llm.openai_client import OpenAIClient
from app.services.conversation import ConversationService
from app.services.tool_registry import ToolRegistry
from app.services.exceptions import ConversationNotFoundError

MAX_ITERATIONS = 5
FALLBACK_MESSAGE = "I apologize, but I exceeded the maximum number of tool execution steps before arriving at a final response."


class AgentService:
    """
    Orchestrates the multi-turn tool-calling agent loop.
    """

    def __init__(
        self,
        session: AsyncSession,
        llm_client: LLMClient | None = None,
    ):
        self.session = session
        self.conversations = ConversationService(session)
        self.llm = llm_client or OpenAIClient()

    async def execute_turn(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        message: str,
    ) -> str:
        """
        Execute one full conversation turn (non-streaming).
        """
        conversation = await self.conversations.get_conversation(
            conversation_id=conversation_id,
            user_id=user_id,
        )
        if conversation is None:
            raise ConversationNotFoundError()

        # 1. Add user message
        await self.conversations.add_user_message(conversation_id, message)

        registry = ToolRegistry(db=self.session, user_id=user_id)
        tools = registry.get_schemas()

        final_content = FALLBACK_MESSAGE

        # 2. Agent tool loop
        for _ in range(MAX_ITERATIONS):
            history = await self.conversations.get_messages(conversation_id, user_id)
            response = await self.llm.generate(history, tools=tools)

            if response.stop_reason == "tool_use" and response.tool_calls:
                for tool_call in response.tool_calls:
                    # Execute tool safely
                    tool_result = await registry.execute_tool(
                        tool_call.name, tool_call.arguments
                    )
                    # Persist tool execution message
                    await self.conversations.add_tool_message(
                        conversation_id=conversation_id,
                        tool_name=tool_call.name,
                        tool_call_id=tool_call.id,
                        tool_input=tool_call.arguments,
                        tool_output=tool_result,
                    )
                continue

            # LLM provided final answer or no tool calls
            final_content = response.content or ""
            break

        # 3. Add assistant final response
        await self.conversations.add_assistant_message(conversation_id, final_content)
        await self.session.commit()

        return final_content

    async def stream_turn(
        self,
        *,
        conversation_id: UUID,
        user_id: UUID,
        message: str,
    ) -> AsyncIterator[str]:
        """
        Execute one full conversation turn streaming formatted SSE events.
        Events emitted:
        - event: tool_call
        - event: tool_result
        - event: token
        - event: done
        """
        try:
            conversation = await self.conversations.get_conversation(
                conversation_id=conversation_id,
                user_id=user_id,
            )
        except ConversationNotFoundError:
            yield f"event: error\ndata: {json.dumps({'message': 'Conversation not found'})}\n\n"
            return

        # 1. Add user message
        await self.conversations.add_user_message(conversation_id, message)

        registry = ToolRegistry(db=self.session, user_id=user_id)
        tools = registry.get_schemas()

        final_content = ""

        # 2. Agent tool loop
        for iteration in range(MAX_ITERATIONS):
            history = await self.conversations.get_messages(conversation_id, user_id)
            response = await self.llm.generate(history, tools=tools)

            if response.stop_reason == "tool_use" and response.tool_calls:
                for tool_call in response.tool_calls:
                    yield f"event: tool_call\ndata: {json.dumps({'name': tool_call.name, 'input': tool_call.arguments})}\n\n"

                    tool_result = await registry.execute_tool(
                        tool_call.name, tool_call.arguments
                    )
                    yield f"event: tool_result\ndata: {json.dumps({'name': tool_call.name, 'output': tool_result})}\n\n"

                    await self.conversations.add_tool_message(
                        conversation_id=conversation_id,
                        tool_name=tool_call.name,
                        tool_call_id=tool_call.id,
                        tool_input=tool_call.arguments,
                        tool_output=tool_result,
                    )
                continue

            final_content = response.content or ""
            break
        else:
            final_content = FALLBACK_MESSAGE

        # Emit token chunks
        for token in final_content.split(" "):
            yield f"event: token\ndata: {json.dumps({'delta': token + ' '})}\n\n"

        # Add final assistant message & emit done
        await self.conversations.add_assistant_message(conversation_id, final_content)
        await self.session.commit()

        yield f"event: done\ndata: {json.dumps({'status': 'completed'})}\n\n"