import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_tasks_crud(client: AsyncClient, test_user: tuple[User, str]):
    _, raw_key = test_user
    headers = {"X-API-Key": raw_key}

    # 1. Create task
    res = await client.post("/api/v1/tasks", json={"title": "Buy groceries"}, headers=headers)
    assert res.status_code == 201
    task = res.json()
    task_id = task["id"]
    assert task["is_done"] is False

    # 2. List tasks
    res = await client.get("/api/v1/tasks", headers=headers)
    assert res.status_code == 200
    assert res.json()["total"] == 1

    # 3. Patch task (mark completed)
    res = await client.patch(f"/api/v1/tasks/{task_id}", json={"is_done": True}, headers=headers)
    assert res.status_code == 200
    assert res.json()["is_done"] is True

    # 4. Delete task
    res = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert res.status_code == 204
