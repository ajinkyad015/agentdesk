"""
LLM package: provider abstraction for language model clients.

- client.py     — LLMClient Protocol, LLMResponse, LLMToolCall dataclasses
- openai_client.py — OpenAI implementation
- fake_client.py   — Scripted mock for deterministic testing (zero API cost)
"""
from app.llm.client import LLMClient, LLMResponse, LLMToolCall
from app.llm.fake_client import FakeLLMClient
from app.llm.openai_client import OpenAIClient

__all__ = ["LLMClient", "LLMResponse", "LLMToolCall", "FakeLLMClient", "OpenAIClient"]
