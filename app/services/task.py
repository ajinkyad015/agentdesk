from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.task import Task
from app.repositories.task import TaskRepository
from app.schemas.task import TaskCreate, TaskUpdate
from app.services.exceptions import TaskNotFoundError


class TaskService:
    """
    Business logic for user To-Do tasks.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.task_repo = TaskRepository(session)

    async def list_tasks(
        self,
        user_id: UUID,
        *,
        is_done: bool | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Task]:
        return await self.task_repo.get_user_tasks(
            user_id,
            is_done=is_done,
            offset=offset,
            limit=limit,
        )

    async def get_task(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> Task:
        task = await self.task_repo.get_user_task(task_id, user_id)
        if task is None:
            raise TaskNotFoundError()
        return task

    async def create_task(
        self,
        user_id: UUID,
        data: TaskCreate,
    ) -> Task:
        task = await self.task_repo.create_task(
            user_id=user_id,
            title=data.title,
            due_date=data.due_date,
        )
        await self.session.commit()
        await self.session.refresh(task)
        return task

    async def update_task(
        self,
        task_id: UUID,
        user_id: UUID,
        data: TaskUpdate,
    ) -> Task:
        task = await self.get_task(task_id, user_id)
        updated = await self.task_repo.update_task(
            task,
            title=data.title,
            is_done=data.is_done,
            due_date=data.due_date,
        )
        await self.session.commit()
        await self.session.refresh(updated)
        return updated

    async def delete_task(
        self,
        task_id: UUID,
        user_id: UUID,
    ) -> None:
        task = await self.get_task(task_id, user_id)
        await self.task_repo.delete(task)
        await self.session.commit()
