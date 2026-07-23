from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import Field

from app.schemas.common import SchemaModel, UUIDSchema, TimestampSchema


class TaskCreate(SchemaModel):
    """
    Request body for creating a task.
    """

    title: str = Field(
        min_length=1,
        max_length=255,
    )

    due_date: datetime | None = Field(
        default=None,
        description="Optional due date for the task",
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

    is_done: bool | None = Field(
        default=None,
        description="Completion status",
    )

    due_date: datetime | None = Field(
        default=None,
        description="Due date for the task",
    )


class TaskResponse(UUIDSchema, TimestampSchema):
    """
    Response model for a task.
    """

    user_id: UUID
    title: str
    is_done: bool
    due_date: datetime | None = None


class TaskListResponse(SchemaModel):
    """
    Response model for a list of tasks.
    """

    items: list[TaskResponse]
    total: int