from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import (
    get_current_active_user,
    get_current_superuser,
    get_current_user,
)
from app.db.session import get_db
from app.models.user import User
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
# Authentication
# ---------------------------------------------------------------------

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]

CurrentActiveUser = Annotated[
    User,
    Depends(get_current_active_user),
]

CurrentSuperUser = Annotated[
    User,
    Depends(get_current_superuser),
]