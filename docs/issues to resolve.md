# 1. Register the router

In app/api/v1/__init__.py or wherever your routers are assembled:

from app.api.v1.routers.auth import router as auth_router

api_router.include_router(auth_router)