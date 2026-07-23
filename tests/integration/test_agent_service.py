import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.llm.client import LLMResponse, LLMToolCall
from app.llm.fake_client import FakeLLMClient
from app.models.user import User
from app.services.agent import AgentService
from app.services.conversation import ConversationService


@pytest.mark.asyncio
async def test_agent_tool_calling_loop(db_session: AsyncSession, test_user: tuple[User, str]):
    user, _ = test_user
    conv_service = ConversationService(db_session)
    conversation = await conv_service.create_conversation(user_id=user.id, title="Test Loop")

    # Scripted fake responses:
    # 1st response: requests calculate tool
    # 2nd response: returns final answer
    fake_responses = [
        LLMResponse(
            content=None,
            tool_calls=[LLMToolCall(id="call_1", name="calculate", arguments={"expression": "10 + 20"})],
            stop_reason="tool_use",
        ),
        LLMResponse(
            content="The result of 10 + 20 is 30.",
            tool_calls=[],
            stop_reason="end_turn",
        ),
    ]
    fake_client = FakeLLMClient(responses=fake_responses)
    agent_service = AgentService(session=db_session, llm_client=fake_client)

    result = await agent_service.execute_turn(
        conversation_id=conversation.id,
        user_id=user.id,
        message="What is 10 + 20?",
    )

    assert "30" in result

    # Check conversation message history
    messages = await conv_service.get_messages(conversation.id, user.id)
    # Expected messages: User -> Tool -> Assistant
    roles = [m.role.value for m in messages]
    assert roles == ["user", "tool", "assistant"]
    assert messages[1].tool_name == "calculate"
    assert messages[1].tool_output.get("result") == 30
