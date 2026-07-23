from __future__ import annotations

from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.auth.service import AuthService
from app.db.session import get_db
from app.models.user import User
from app.services.agent import AgentService
from app.services.conversation import ConversationService
from app.services.task import TaskService

# ---------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------

DBSession = Annotated[
    AsyncSession,
    Depends(get_db),
]


# ---------------------------------------------------------------------
# Services Dependencies
# ---------------------------------------------------------------------

def get_conversation_service(
    db: DBSession,
) -> ConversationService:
    return ConversationService(db)


ConversationServiceDep = Annotated[
    ConversationService,
    Depends(get_conversation_service),
]


def get_task_service(
    db: DBSession,
) -> TaskService:
    return TaskService(db)


TaskServiceDep = Annotated[
    TaskService,
    Depends(get_task_service),
]


def get_agent_service(
    db: DBSession,
) -> AgentService:
    return AgentService(db)


AgentServiceDep = Annotated[
    AgentService,
    Depends(get_agent_service),
]


def get_auth_service(
    db: DBSession,
) -> AuthService:
    return AuthService(db)


AuthServiceDep = Annotated[
    AuthService,
    Depends(get_auth_service),
]


# ---------------------------------------------------------------------
# Authentication Dependency
# ---------------------------------------------------------------------

CurrentUser = Annotated[
    User,
    Depends(get_current_user),
]