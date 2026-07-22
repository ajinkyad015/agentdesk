from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User


@dataclass(slots=True)
class AuthenticationResult:
    """
    Result returned after successful authentication.
    """

    user: User
    access_token: str
    refresh_token: str