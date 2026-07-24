from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.logging import configure_logging, logger
from app.middleware.request_id import RequestIDMiddleware

from app.api.v1.routers import api_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application startup and shutdown lifecycle.

    Runs once when the application starts and once before it exits.
    """

    configure_logging()

    logger.info(
        "Starting application",
        extra={
            "app_name": settings.APP_NAME,
            "version": settings.APP_VERSION,
            "debug": settings.DEBUG,
        },
    )

    yield

    logger.info("Shutting down application")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-grade Tool Calling AI Agent Backend",
    debug=settings.DEBUG,
    lifespan=lifespan,
    openapi_url=f"{settings.API_PREFIX}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
)

# -------------------------------------------------------------------
# Middleware
# -------------------------------------------------------------------

app.add_middleware(RequestIDMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# -------------------------------------------------------------------
# Routers
# -------------------------------------------------------------------


app.include_router(
    api_router,
    prefix=settings.API_PREFIX,
)

# -------------------------------------------------------------------
# Static Frontend (served at /ui)
# -------------------------------------------------------------------

_frontend_dir = Path(__file__).resolve().parent.parent / "frontend"
if _frontend_dir.is_dir():
    app.mount("/ui", StaticFiles(directory=str(_frontend_dir), html=True), name="frontend")


@app.get("/", tags=["Root"])
async def root():
    """
    Root endpoint.
    """

    return {
        "application": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "docs": "/docs",
        "ui": "/ui",
        "health": f"{settings.API_PREFIX}/health",
    }