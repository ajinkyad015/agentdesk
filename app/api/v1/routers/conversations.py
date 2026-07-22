from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import (
    ConversationServiceDep,
    CurrentActiveUser,
)
from app.models.user import User
from app.schemas.conversation import (
    ConversationCreate,
    ConversationListResponse,
    ConversationResponse,
    ConversationUpdate,
)
from app.services.exceptions import ConversationNotFoundError 

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
)
@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    payload: ConversationCreate,
    current_user: CurrentActiveUser,
    service: ConversationServiceDep,
) -> ConversationResponse:
    """
    Create a new conversation.
    """

    conversation = await service.create_conversation(
        user_id=current_user.id,
        title=payload.title,
    )

    return conversation


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
    current_user: CurrentActiveUser,
    service: ConversationServiceDep,
) -> ConversationListResponse:
    """
    Return all conversations for the current user.
    """

    conversations = await service.list_conversations(
        current_user.id,
    )
    if conversations is None:
        raise ConversationNotFoundError()

    return ConversationListResponse(
        items=conversations,
        total=len(conversations),
    )



@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: UUID,
    current_user: CurrentActiveUser,
    service: ConversationServiceDep,
) -> ConversationResponse:
    """
    Return a single conversation.
    """

    try:
        return await service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
@router.patch(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def update_conversation(
    conversation_id: UUID,
    payload: ConversationUpdate,
    current_user: CurrentActiveUser,
    service: ConversationServiceDep,
) -> ConversationResponse:
    """
    Update a conversation.
    """

    try:
        return await service.update_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            data=payload,
        )

    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )
@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_conversation(
    conversation_id: UUID,
    current_user: CurrentActiveUser,
    service: ConversationServiceDep,
) -> Response:
    """
    Delete a conversation.
    """

    try:
        await service.delete_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )

    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return Response(
        status_code=status.HTTP_204_NO_CONTENT,
    )