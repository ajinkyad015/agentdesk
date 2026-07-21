from __future__ import annotations

from typing import Any

from pydantic import Field

from app.models.enums import TaskStatus
from app.schemas.common import BaseResponse, SchemaModel


class TaskCreate(SchemaModel):
    """
    Request body for creating a background task.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10_000,
    )


class TaskUpdate(SchemaModel):
    """
    Request body for updating a task.
    """

    title: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
    )

    description: str | None = Field(
        default=None,
        max_length=10_000,
    )


class TaskResponse(BaseResponse):
    title: str
    description: str | None

    status: TaskStatus

    progress: int = Field(
        ge=0,
        le=100,
        default=0,
    )

    current_step: str | None = None

    result: dict[str, Any] | None = None

    error: str | None = None

class TaskListResponse(SchemaModel):
    """
    Response model for a paginated task list.
    """

    items: list[TaskResponse]

    total: int