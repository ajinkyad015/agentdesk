from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import ConversationServiceDep, CurrentUser
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
    current_user: CurrentUser,
    service: ConversationServiceDep,
) -> ConversationResponse:
    """
    Create a new conversation.
    """
    conversation = await service.create_conversation(
        user_id=current_user.id,
        title=payload.title,
    )
    return ConversationResponse.model_validate(conversation)


@router.get(
    "",
    response_model=ConversationListResponse,
)
async def list_conversations(
    current_user: CurrentUser,
    service: ConversationServiceDep,
) -> ConversationListResponse:
    """
    List all conversations for the authenticated user.
    """
    items = await service.list_conversations(current_user.id)
    return ConversationListResponse(
        items=[ConversationResponse.model_validate(c) for c in items],
        total=len(items),
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationResponse,
)
async def get_conversation(
    conversation_id: UUID,
    current_user: CurrentUser,
    service: ConversationServiceDep,
) -> ConversationResponse:
    """
    Get a specific conversation by ID.
    """
    try:
        conversation = await service.get_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
        )
        return ConversationResponse.model_validate(conversation)
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
    current_user: CurrentUser,
    service: ConversationServiceDep,
) -> ConversationResponse:
    """
    Update a conversation title.
    """
    try:
        conversation = await service.update_conversation(
            conversation_id=conversation_id,
            user_id=current_user.id,
            data=payload,
        )
        return ConversationResponse.model_validate(conversation)
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
    current_user: CurrentUser,
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
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except ConversationNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )