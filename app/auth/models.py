from __future__ import annotations

from dataclasses import dataclass

from app.models.user import User


@dataclass(slots=True)
class AuthenticationResult:
    """
    Result returned after successful authentication via API key.
    """

    user: User
    api_key: str  # The raw API key, shown once at registration