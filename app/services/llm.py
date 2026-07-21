from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from openai import AsyncOpenAI

from app.core.config import settings
from app.models.enums import MessageRole
from app.models.message import Message


@dataclass(slots=True)
class LLMResponse:
    """
    Standard response returned by every LLM provider.
    """

    content: str
    model: str
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class LLMProvider(Protocol):
    """
    Interface implemented by every LLM provider.
    """

    async def generate(
        self,
        messages: list[Message],
    ) -> LLMResponse: ...


class OpenAIProvider:
    """
    OpenAI implementation.
    """

    model=settings.OPENAI_MODEL

    def __init__(self) -> None:
        self.client = AsyncOpenAI(
            api_key=settings.OPENAI_API_KEY,
        )

    # async def generate(
    #     self,
    #     messages: list[Message],
    # ) -> LLMResponse:
    #     response = await self.client.chat.completions.create(
    #         model=self.model,
    #         messages=[
    #             {
    #                 "role": self._role(message),
    #                 "content": message.content,
    #             }
    #             for message in messages
    #         ],
    #     )

    #     choice = response.choices[0]
    #     usage = response.usage

    #     return LLMResponse(
    #         content=choice.message.content or "",
    #         model=response.model,
    #         prompt_tokens=usage.prompt_tokens if usage else 0,
    #         completion_tokens=usage.completion_tokens if usage else 0,
    #         total_tokens=usage.total_tokens if usage else 0,
    #     )

    @staticmethod
    def _role(message: Message) -> str:
        """
        Convert our enum into OpenAI roles.
        """
        return message.role.value


class LLMService:
    """
    High-level facade used by the application.
    """

    def __init__(
        self,
        provider: LLMProvider | None = None,
    ) -> None:
        self.provider = provider or OpenAIProvider()

    async def generate(
        self,
        messages: list[Message],
    ) -> LLMResponse:
        return await self.provider.generate(messages)