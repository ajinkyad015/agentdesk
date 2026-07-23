from __future__ import annotations


class ServiceError(Exception):
    """Base class for all service-layer exceptions."""
    pass


class ResourceNotFoundError(ServiceError):
    """Raised when a requested resource does not exist."""
    pass


class ConversationNotFoundError(ResourceNotFoundError):
    """Raised when a conversation cannot be found."""
    pass


class TaskNotFoundError(ResourceNotFoundError):
    """Raised when a task cannot be found."""
    pass


class PermissionDeniedError(ServiceError):
    """Raised when the current user cannot access a resource."""
    pass


class ConflictError(ServiceError):
    """Raised when an operation conflicts with the current state."""
    pass


class ValidationError(ServiceError):
    """Raised when business validation fails."""
    pass