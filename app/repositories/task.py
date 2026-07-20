from __future__ import annotations

from uuid import UUID

from sqlalchemy import select

from app.models.enums import TaskStatus
from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    Repository for Task-specific database operations.
    """

    def __init__(self, session):
        super().__init__(session, Task)

    async def get_user_tasks(
        self,
        user_id: UUID,
        *,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """
        Return all tasks for a user.
        """
        stmt = (
            select(Task)
            .where(Task.user_id == user_id)
            .order_by(Task.created_at.desc())
            .offset(offset)
            .limit(limit)
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_pending_tasks(self) -> list[Task]:
        """
        Return every pending task.
        """
        stmt = (
            select(Task)
            .where(Task.status == TaskStatus.PENDING)
            .order_by(Task.created_at.asc())
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def get_running_tasks(self) -> list[Task]:
        """
        Return all currently running tasks.
        """
        stmt = (
            select(Task)
            .where(Task.status == TaskStatus.RUNNING)
            .order_by(Task.created_at.asc())
        )

        result = await self.session.execute(stmt)

        return list(result.scalars().all())

    async def mark_running(
        self,
        task: Task,
    ) -> Task:
        """
        Mark a task as running.
        """
        task.status = TaskStatus.RUNNING

        await self.session.flush()
        await self.session.refresh(task)

        return task

    async def mark_completed(
        self,
        task: Task,
        result_data: dict,
    ) -> Task:
        """
        Mark a task as completed.
        """
        task.status = TaskStatus.COMPLETED
        task.result = result_data
        task.error = None

        await self.session.flush()
        await self.session.refresh(task)

        return task

    async def mark_failed(
        self,
        task: Task,
        error: str,
    ) -> Task:
        """
        Mark a task as failed.
        """
        task.status = TaskStatus.FAILED
        task.error = error

        await self.session.flush()
        await self.session.refresh(task)

        return task