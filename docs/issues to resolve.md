# 1. Register the router

In app/api/v1/__init__.py or wherever your routers are assembled:

from app.api.v1.routers.auth import router as auth_router

api_router.include_router(auth_router)

## what iam focusing for this commit:
1. only focusing on r refctoring propossed by main chat( in that what we are focusing is in docs/auth_chat_refactor.md)

# there is no router in or main app do we will ad it later
