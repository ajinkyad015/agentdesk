from fastapi import APIRouter

from app.api.v1.routers.auth import router as auth_router
from app.api.v1.routers.conversations import router as conversations_router
from app.api.v1.routers.health import router as health_router
from app.api.v1.routers.messages import router as messages_router
from app.api.v1.routers.tasks import router as tasks_router

api_router = APIRouter()

api_router.include_router(health_router)
api_router.include_router(auth_router)
api_router.include_router(conversations_router)
api_router.include_router(messages_router)
api_router.include_router(tasks_router)