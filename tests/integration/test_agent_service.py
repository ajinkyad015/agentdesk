"""
Integration tests for the AgentService loop with FakeLLMClient.

Tests:
- Single tool call (calculate) end-to-end
- Multi-tool chain (calculate → create_task)
- Iteration cap fallback (loop exceeds MAX_ITERATIONS)
- Tool error does not crash the loop (graceful recovery)
- SSE streaming produces well-formed events
"""

from __future__ import annotations

import json
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMResponse, LLMToolCall
from app.llm.fake_client import FakeLLMClient
from app.models.user import User
from app.services.agent import MAX_ITERATIONS, AgentService, FALLBACK_MESSAGE
from app.services.conversation import ConversationService


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _new_conv(db: AsyncSession, user: User, title: str = "Test Conv"):
    svc = ConversationService(db)
    return await svc.create_conversation(user_id=user.id, title=title)


def _tool_response(name: str, args: dict, call_id: str = "call_1") -> LLMResponse:
    return LLMResponse(
        content=None,
        tool_calls=[LLMToolCall(id=call_id, name=name, arguments=args)],
        stop_reason="tool_use",
    )


def _final_response(text: str) -> LLMResponse:
    return LLMResponse(
        content=text,
        tool_calls=[],
        stop_reason="end_turn",
    )


# ---------------------------------------------------------------------------
# Single tool call
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_single_tool_call_calculate(
    db_session: AsyncSession, test_user: tuple[User, str]
) -> None:
    user, _ = test_user
    conv = await _new_conv(db_session, user, "Calc")

    fake = FakeLLMClient(responses=[
        _tool_response("calculate", {"expression": "10 + 20"}),
        _final_response("The answer is 30."),
    ])
    agent = AgentService(session=db_session, llm_client=fake)

    result = await agent.execute_turn(
        conversation_id=conv.id,
        user_id=user.id,
        message="What is 10 + 20?",
    )

    assert "30" in result

    svc = ConversationService(db_session)
    messages = await svc.get_messages(conv.id, user.id)
    roles = [m.role.value for m in messages]
    assert roles == ["user", "tool", "assistant"]
    tool_msg = messages[1]
    assert tool_msg.tool_name == "calculate"
    assert tool_msg.tool_output.get("result") == 30


# ---------------------------------------------------------------------------
# Multi-step tool chain
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_two_sequential_tool_calls(
    db_session: AsyncSession, test_user: tuple[User, str]
) -> None:
    """Verify the loop handles two sequential tool calls before a final answer."""
    user, _ = test_user
    conv = await _new_conv(db_session, user, "Multi-Tool")

    fake = FakeLLMClient(responses=[
        _tool_response("calculate", {"expression": "5 * 5"}, call_id="call_1"),
        _tool_response("create_task", {"title": "Remember: 5*5=25"}, call_id="call_2"),
        _final_response("Done! 5*5=25 and I created a task for you."),
    ])
    agent = AgentService(session=db_session, llm_client=fake)

    result = await agent.execute_turn(
        conversation_id=conv.id,
        user_id=user.id,
        message="Calculate 5*5 and make a task about it.",
    )

    assert "25" in result or "Done" in result

    svc = ConversationService(db_session)
    messages = await svc.get_messages(conv.id, user.id)
    roles = [m.role.value for m in messages]
    tool_names = [m.tool_name for m in messages if m.tool_name]
    assert "calculate" in tool_names
    assert "create_task" in tool_names
    assert "assistant" in roles


# ---------------------------------------------------------------------------
# Iteration cap fallback
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_iteration_cap_returns_fallback(
    db_session: AsyncSession, test_user: tuple[User, str]
) -> None:
    """
    When the loop hits MAX_ITERATIONS without a final text answer,
    it must emit the FALLBACK_MESSAGE and never raise an exception.
    """
    user, _ = test_user
    conv = await _new_conv(db_session, user, "Infinite Loop")

    # All responses keep requesting tool calls — loop never terminates naturally
    infinite_responses = [
        _tool_response("calculate", {"expression": "1+1"}, call_id=f"call_{i}")
        for i in range(MAX_ITERATIONS + 2)
    ]
    fake = FakeLLMClient(responses=infinite_responses)
    agent = AgentService(session=db_session, llm_client=fake)

    result = await agent.execute_turn(
        conversation_id=conv.id,
        user_id=user.id,
        message="Enter infinite loop please.",
    )

    assert result == FALLBACK_MESSAGE


# ---------------------------------------------------------------------------
# Unknown tool name — graceful error
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_unknown_tool_name_is_handled(
    db_session: AsyncSession, test_user: tuple[User, str]
) -> None:
    """
    If the LLM requests a tool that doesn't exist, the registry returns
    an error dict. The loop should recover and not crash.
    """
    user, _ = test_user
    conv = await _new_conv(db_session, user, "Bad Tool")

    fake = FakeLLMClient(responses=[
        _tool_response("nonexistent_tool", {"arg": "val"}),
        _final_response("I tried a tool that doesn't exist but recovered."),
    ])
    agent = AgentService(session=db_session, llm_client=fake)

    result = await agent.execute_turn(
        conversation_id=conv.id,
        user_id=user.id,
        message="Use a tool that doesn't exist.",
    )

    # Should not raise; either fallback or final response
    assert isinstance(result, str)

    # The tool message should record the error output
    svc = ConversationService(db_session)
    messages = await svc.get_messages(conv.id, user.id)
    tool_msgs = [m for m in messages if m.tool_name == "nonexistent_tool"]
    assert len(tool_msgs) == 1
    assert "error" in tool_msgs[0].tool_output


# ---------------------------------------------------------------------------
# SSE stream: well-formed events
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stream_turn_emits_well_formed_sse_events(
    db_session: AsyncSession, test_user: tuple[User, str]
) -> None:
    """
    stream_turn must produce:
    - At least one 'event: token' block
    - Exactly one 'event: done' block
    - Zero 'event: error' blocks (for a valid conversation)
    - All data lines must be valid JSON
    """
    user, _ = test_user
    conv = await _new_conv(db_session, user, "SSE Test")

    fake = FakeLLMClient(responses=[
        _final_response("Hello world from the agent."),
    ])
    agent = AgentService(session=db_session, llm_client=fake)

    events: list[str] = []
    async for chunk in agent.stream_turn(
        conversation_id=conv.id,
        user_id=user.id,
        message="Say hello.",
    ):
        events.append(chunk)

    full = "".join(events)

    assert "event: token" in full
    assert full.count("event: done") == 1
    assert "event: error" not in full

    # All data: lines must contain valid JSON
    for line in full.splitlines():
        if line.startswith("data: "):
            payload = line[6:]
            parsed = json.loads(payload)  # raises if invalid JSON
            assert isinstance(parsed, dict)


# ---------------------------------------------------------------------------
# SSE stream: tool_call and tool_result events
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_stream_turn_emits_tool_events(
    db_session: AsyncSession, test_user: tuple[User, str]
) -> None:
    """When a tool is called, the stream must include tool_call and tool_result events."""
    user, _ = test_user
    conv = await _new_conv(db_session, user, "SSE Tool Events")

    fake = FakeLLMClient(responses=[
        _tool_response("calculate", {"expression": "7 * 6"}),
        _final_response("7 times 6 is 42."),
    ])
    agent = AgentService(session=db_session, llm_client=fake)

    chunks: list[str] = []
    async for chunk in agent.stream_turn(
        conversation_id=conv.id,
        user_id=user.id,
        message="What is 7 * 6?",
    ):
        chunks.append(chunk)

    full = "".join(chunks)

    assert "event: tool_call" in full
    assert "event: tool_result" in full
    assert "event: done" in full
    assert "event: error" not in full
