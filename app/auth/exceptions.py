from __future__ import annotations


class AuthenticationError(Exception):
    """Base authentication exception."""


class InvalidCredentialsError(AuthenticationError):
    """Invalid email or password."""


class UserAlreadyExistsError(AuthenticationError):
    """Email already registered."""


class InactiveUserError(AuthenticationError):
    """User account is inactive."""


class InvalidTokenError(AuthenticationError):
    """Token is invalid."""


class TokenExpiredError(AuthenticationError):
    """Token has expired."""