from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Protocol

from app.models.message import Message


@dataclass(slots=True)
class LLMToolCall:
    id: str
    name: str
    arguments: dict[str, Any]


@dataclass(slots=True)
class LLMResponse:
    content: str | None
    tool_calls: list[LLMToolCall]
    stop_reason: str  # "end_turn", "tool_use", etc.
    model: str = ""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class LLMClient(Protocol):
    async def generate(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> LLMResponse:
        ...

    def stream(
        self,
        messages: list[Message],
        tools: list[dict[str, Any]] | None = None,
    ) -> AsyncIterator[str]:
        ...
