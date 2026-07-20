from datetime import  datetime

from fastapi import APIRouter

from app.core.config import settings

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health Check",
    description="Returns the current health status of the application.",
)
async def health_check() -> dict[str, str]:
    """
    Basic health check endpoint.
    """

    return {
        "status": "ok",
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "timestamp": datetime.now().isoformat(),
    }