from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.services.agent import AgentService
from app.services.conversation import ConversationService


# ---------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------

DBSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


# ---------------------------------------------------------------------
# Services
# ---------------------------------------------------------------------

def get_conversation_service(
    db: DBSession,
) -> ConversationService:
    """
    Dependency that returns a ConversationService.
    """
    return ConversationService(db)


ConversationServiceDep = Annotated[
    ConversationService,
    Depends(get_conversation_service),
]


def get_agent_service(
    db: DBSession,
) -> AgentService:
    """
    Dependency that returns an AgentService.
    """
    return AgentService(db)


AgentServiceDep = Annotated[
    AgentService,
    Depends(get_agent_service),
]


# ---------------------------------------------------------------------
# Authentication (Temporary)
# ---------------------------------------------------------------------

async def get_current_user_id() -> UUID:
    """
    Temporary authentication dependency.

    This will be replaced by JWT authentication.
    """

    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Authentication has not been implemented.",
    )


CurrentUserID = Annotated[
    UUID,
    Depends(get_current_user_id),
]