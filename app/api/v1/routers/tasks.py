from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, HTTPException, Response, status

from app.api.deps import CurrentUser, TaskServiceDep
from app.schemas.task import (
    TaskCreate,
    TaskListResponse,
    TaskResponse,
    TaskUpdate,
)
from app.services.exceptions import TaskNotFoundError

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"],
)


@router.get(
    "",
    response_model=TaskListResponse,
)
async def list_tasks(
    current_user: CurrentUser,
    service: TaskServiceDep,
    is_done: bool | None = None,
) -> TaskListResponse:
    """
    List user tasks.
    """
    tasks = await service.list_tasks(current_user.id, is_done=is_done)
    return TaskListResponse(
        items=[TaskResponse.model_validate(t) for t in tasks],
        total=len(tasks),
    )


@router.post(
    "",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_task(
    payload: TaskCreate,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> TaskResponse:
    """
    Create a new task.
    """
    task = await service.create_task(current_user.id, payload)
    return TaskResponse.model_validate(task)


@router.patch(
    "/{task_id}",
    response_model=TaskResponse,
)
async def update_task(
    task_id: UUID,
    payload: TaskUpdate,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> TaskResponse:
    """
    Update a task (e.g. mark done or update title).
    """
    try:
        task = await service.update_task(
            task_id=task_id,
            user_id=current_user.id,
            data=payload,
        )
        return TaskResponse.model_validate(task)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_task(
    task_id: UUID,
    current_user: CurrentUser,
    service: TaskServiceDep,
) -> Response:
    """
    Delete a task.
    """
    try:
        await service.delete_task(task_id=task_id, user_id=current_user.id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except TaskNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found",
        )
