import uuid
from contextvars import ContextVar

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

# Context variable shared during one request lifecycle
request_id_ctx_var: ContextVar[str] = ContextVar(
    "request_id",
    default=""
)


class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds a unique request ID to every incoming request.
    """ 

    async def dispatch(self, request: Request, call_next):
        request_id = str(uuid.uuid4())

        # Store in ContextVar
        request_id_ctx_var.set(request_id)

        # Make it available via request.state as well
        request.state.request_id = request_id

        response = await call_next(request)

        # Include request ID in every response
        response.headers["X-Request-ID"] = request_id

        return response