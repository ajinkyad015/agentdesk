from __future__ import annotations

from typing import Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.task import TaskCreate, TaskUpdate
from app.services.task import TaskService


async def create_task(
    db: AsyncSession,
    user_id: UUID,
    title: str,
) -> dict[str, Any]:
    service = TaskService(db)
    task = await service.create_task(user_id=user_id, data=TaskCreate(title=title))
    return {
        "id": str(task.id),
        "title": task.title,
        "is_done": task.is_done,
        "created_at": task.created_at.isoformat(),
    }


async def list_tasks(
    db: AsyncSession,
    user_id: UUID,
    is_done: bool | None = None,
) -> dict[str, Any]:
    service = TaskService(db)
    tasks = await service.list_tasks(user_id=user_id, is_done=is_done)
    return {
        "tasks": [
            {
                "id": str(t.id),
                "title": t.title,
                "is_done": t.is_done,
                "due_date": t.due_date.isoformat() if t.due_date else None,
            }
            for t in tasks
        ],
        "total": len(tasks),
    }


async def complete_task(
    db: AsyncSession,
    user_id: UUID,
    task_id: str,
) -> dict[str, Any]:
    try:
        uuid_id = UUID(task_id)
        service = TaskService(db)
        task = await service.update_task(
            task_id=uuid_id,
            user_id=user_id,
            data=TaskUpdate(is_done=True),
        )
        return {
            "id": str(task.id),
            "title": task.title,
            "is_done": task.is_done,
        }
    except Exception as e:
        return {"error": f"Failed to complete task: {str(e)}"}
