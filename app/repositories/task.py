from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.base import BaseRepository


class TaskRepository(BaseRepository[Task]):
    """
    Repository for Task database operations.
    """

    def __init__(self, session: AsyncSession):
        super().__init__(session=session, model=Task)

    async def get_user_tasks(
        self,
        user_id: UUID,
        *,
        is_done: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        """
        Return tasks for a user, optionally filtered by status.
        """
        stmt = select(Task).where(Task.user_id == user_id)

        if is_done is not None:
            stmt = stmt.where(Task.is_done == is_done)

        stmt = stmt.order_by(Task.created_at.desc()).offset(offset).limit(limit)

        result = await self.session.execute(stmt)
        return list(result.scalars().all())

    async def get_user_task(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> Task | None:
        stmt = select(Task).where(
            Task.id == task_id,
            Task.user_id == user_id,
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def create_task(
        self,
        *,
        user_id: UUID,
        title: str,
        due_date: datetime | None = None,
    ) -> Task:
        task = Task(
            user_id=user_id,
            title=title,
            due_date=due_date,
            is_done=False,
        )
        self.session.add(task)
        await self.session.flush()
        await self.session.refresh(task)
        return task

    async def update_task(
        self,
        task: Task,
        *,
        title: str | None = None,
        is_done: bool | None = None,
        due_date: datetime | None = None,
    ) -> Task:
        if title is not None:
            task.title = title
        if is_done is not None:
            task.is_done = is_done
        if due_date is not None:
            task.due_date = due_date

        await self.session.flush()
        await self.session.refresh(task)
        return task