class AuthException(Exception):
    """Base exception for authentication errors."""
    pass


class InvalidApiKeyError(AuthException):
    """Raised when an API key is invalid or missing."""
    pass