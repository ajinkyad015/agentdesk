from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from fastapi.responses import StreamingResponse

from app.api.deps import AgentServiceDep, ConversationServiceDep, CurrentUser
from app.schemas.message import MessageCreate, MessageListResponse, MessageResponse
from app.services.exceptions import ConversationNotFoundError

router = APIRouter(
    prefix="/conversations/{conversation_id}/messages",
    tags=["Messages"],
)


@router.get(
    "",
    response_model=MessageListResponse,
)
async def list_messages(
    conversation_id: UUID,
    current_user: CurrentUser,
    service: ConversationServiceDep,
) -> MessageListResponse:
    """
    Get all messages for a conversation.
    """
    try:
        messages = await service.get_messages(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
        return MessageListResponse(
            items=[MessageResponse.model_validate(m) for m in messages],
            total=len(messages),
        )
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )


@router.post(
    "",
    response_class=StreamingResponse,
)
async def send_message(
    conversation_id: UUID,
    payload: MessageCreate,
    current_user: CurrentUser,
    agent_service: AgentServiceDep,
) -> StreamingResponse:
    """
    Send a message to the agent and stream SSE events back.
    """
    generator = agent_service.stream_turn(
        conversation_id=conversation_id,
        user_id=current_user.id,
        message=payload.content,
    )
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )
