from __future__ import annotations

import json
from typing import Any, AsyncIterator

from openai import AsyncOpenAI

from app.core.config import settings
from app.llm.client import LLMClient, LLMResponse, LLMToolCall
from app.models.enums import MessageRole
from app.models.message import Message
from app.prompts.system import SYSTEM_PROMPT


class OpenAIClient:
    """
    OpenAI implementation of LLMClient protocol.
    """

    def __init__(self, api_key: str | None = None, model: str | None = None) -> None:
        self.api_key = api_key or settings.OPENAI_API_KEY
        self.model = model or settings.OPENAI_MODEL
        self.client = AsyncOpenAI(api_key=self.api_key) if self.api_key else None

    def _serialize_messages(self, messages: list[Message]) -> list[dict[str, Any]]:
        api_messages: list[dict[str, Any]] = [{"role": "system", "content": SYSTEM_PROMPT}]

        for msg in messages:
            if msg.role == MessageRole.USER:
                api_messages.append({"role": "user", "content": msg.content})
            elif msg.role == MessageRole.ASSISTANT:
                api_messages.append({"role": "assistant", "content": msg.content})
            elif msg.role == MessageRole.TOOL:
                api_messages.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id or "tool_call_id",
                    "content": json.dumps(msg.tool_output or {}),
                })
        return api_messages

    async def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        if not self.client:
            # Fallback if no API key is provided
            return LLMResponse(
                content="API Key not configured. Please set OPENAI_API_KEY.",
                tool_calls=[],
                stop_reason="end_turn",
                model=self.model,
            )

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._serialize_messages(messages),
        }
        if tools:
            kwargs["tools"] = tools

        response = await self.client.chat.completions.create(**kwargs)
        choice = response.choices[0]
        msg = choice.message
        usage = response.usage

        tool_calls = []
        if msg.tool_calls:
            for tc in msg.tool_calls:
                try:
                    args = json.loads(tc.function.arguments)
                except Exception:
                    args = {}
                tool_calls.append(LLMToolCall(id=tc.id, name=tc.function.name, arguments=args))

        stop_reason = "tool_use" if tool_calls else "end_turn"

        return LLMResponse(
            content=msg.content,
            tool_calls=tool_calls,
            stop_reason=stop_reason,
            model=response.model,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            total_tokens=usage.total_tokens if usage else 0,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str]:
        if not self.client:
            yield "API Key not configured. Please set OPENAI_API_KEY."
            return

        kwargs: dict[str, Any] = {
            "model": self.model,
            "messages": self._serialize_messages(messages),
            "stream": True,
        }
        if tools:
            kwargs["tools"] = tools

        stream = await self.client.chat.completions.create(**kwargs)
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
