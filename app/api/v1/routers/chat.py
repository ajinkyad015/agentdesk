from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import (
    AgentServiceDep,
    CurrentActiveUser,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.exceptions import ConversationNotFoundError

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)


from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from app.api.deps import (
    AgentServiceDep,
    CurrentActiveUser,
)
from app.schemas.chat import (
    ChatRequest,
    ChatResponse,
)
from app.services.exceptions import ConversationNotFoundError

router = APIRouter(
    prefix="/chat",
    tags=["Chat"],
)

