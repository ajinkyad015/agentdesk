from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from jwt import InvalidTokenError

from app.core.config import settings


ACCESS_TOKEN_TYPE = "access"
REFRESH_TOKEN_TYPE = "refresh"


def _create_token(
    *,
    subject: UUID,
    expires_delta: timedelta,
    token_type: str,
) -> str:
    """
    Create a signed JWT.
    """

    now = datetime.now(UTC)

    payload = {
        "sub": str(subject),
        "type": token_type,
        "iat": now,
        "exp": now + expires_delta,
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM,
    )


def create_access_token(user_id: UUID) -> str:
    """
    Create an access token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES,
        ),
        token_type=ACCESS_TOKEN_TYPE,
    )


def create_refresh_token(user_id: UUID) -> str:
    """
    Create a refresh token.
    """

    return _create_token(
        subject=user_id,
        expires_delta=timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS,
        ),
        token_type=REFRESH_TOKEN_TYPE,
    )


def decode_token(token: str) -> dict[str, Any]:
    """
    Decode and validate a JWT.

    Raises:
        jwt.InvalidTokenError
    """

    return jwt.decode(
        token,
        settings.SECRET_KEY,
        algorithms=[settings.ALGORITHM],
    )


def get_token_subject(token: str) -> UUID:
    """
    Extract the user ID from a token.
    """

    payload = decode_token(token)

    return UUID(payload["sub"])


def get_token_type(token: str) -> str:
    """
    Return the token type.
    """

    payload = decode_token(token)

    return payload["type"]


def verify_access_token(token: str) -> UUID:
    """
    Validate an access token and return its subject.
    """

    payload = decode_token(token)

    if payload["type"] != ACCESS_TOKEN_TYPE:
        raise InvalidTokenError("Invalid token type")

    return UUID(payload["sub"])


def verify_refresh_token(token: str) -> UUID:
    """
    Validate a refresh token and return its subject.
    """

    payload = decode_token(token)

    if payload["type"] != REFRESH_TOKEN_TYPE:
        raise InvalidTokenError("Invalid token type")

    return UUID(payload["sub"])