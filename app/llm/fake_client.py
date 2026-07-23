from __future__ import annotations

from typing import Any, AsyncIterator
from app.llm.client import LLMResponse, LLMToolCall
from app.models.message import Message


class FakeLLMClient:
    """
    Scriptable mock LLM client for deterministic testing without external API calls.
    """

    def __init__(self, responses: list[LLMResponse] | None = None):
        self.responses = responses or []
        self.call_count = 0

    async def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        if self.call_count < len(self.responses):
            resp = self.responses[self.call_count]
            self.call_count += 1
            return resp

        # Default fallback response
        last_msg = messages[-1].content if messages else ""
        return LLMResponse(
            content=f"Echo: {last_msg}",
            tool_calls=[],
            stop_reason="end_turn",
            model="fake-model",
            prompt_tokens=10,
            completion_tokens=10,
            total_tokens=20,
        )

    async def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str]:
        resp = await self.generate(messages, tools)
        text = resp.content or "Done"
        for chunk in text.split(" "):
            yield chunk + " "
