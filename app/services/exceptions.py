from __future__ import annotations


class ServiceError(Exception):
    """Base class for all service-layer exceptions."""


class ResourceNotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""


class PermissionDeniedError(ServiceError):
    """Raised when the current user cannot access a resource."""


class ConflictError(ServiceError):
    """Raised when an operation conflicts with the current state."""


class ValidationError(ServiceError):
    """Raised when business validation fails."""

class ServiceError(Exception):
    """Base class for service-layer exceptions."""


class ConversationNotFoundError(ServiceError):
    """Raised when a conversation cannot be found."""