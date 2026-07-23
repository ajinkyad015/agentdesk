import pytest
from httpx import AsyncClient
from app.models.user import User


@pytest.mark.asyncio
async def test_conversations_crud(client: AsyncClient, test_user: tuple[User, str]):
    _, raw_key = test_user
    headers = {"X-API-Key": raw_key}

    # 1. Create conversation
    res = await client.post("/api/v1/conversations", json={"title": "My Chat"}, headers=headers)
    assert res.status_code == 201
    conv = res.json()
    conv_id = conv["id"]
    assert conv["title"] == "My Chat"

    # 2. List conversations
    res = await client.get("/api/v1/conversations", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["items"][0]["id"] == conv_id

    # 3. Get single conversation
    res = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert res.status_code == 200

    # 4. Delete conversation
    res = await client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert res.status_code == 204


@pytest.mark.asyncio
async def test_cross_user_isolation(client: AsyncClient, test_user: tuple[User, str]):
    user1, key1 = test_user

    # Register user 2
    res2 = await client.post("/api/v1/auth/register", json={"display_name": "Bob"})
    key2 = res2.json()["api_key"]

    # User 1 creates conversation
    res = await client.post("/api/v1/conversations", json={"title": "Private"}, headers={"X-API-Key": key1})
    conv_id = res.json()["id"]

    # User 2 tries to read user 1's conversation -> 404
    res_access = await client.get(f"/api/v1/conversations/{conv_id}", headers={"X-API-Key": key2})
    assert res_access.status_code == 404
