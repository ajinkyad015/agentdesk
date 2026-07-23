"""
Comprehensive integration tests for the AgentDesk API.

Covers:
- Auth: registration, missing key, invalid key
- Conversations: full CRUD + cross-user isolation
- Messages: list, SSE stream parsing, conversation-not-found guard
- Tasks: full CRUD + cross-user isolation + filter by is_done
- Health: endpoint shape
"""

from __future__ import annotations

import pytest
from httpx import AsyncClient

from app.models.user import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

async def _register(client: AsyncClient, name: str = "Alice") -> tuple[str, str]:
    """Register a user and return (user_id, api_key)."""
    resp = await client.post("/api/v1/auth/register", json={"display_name": name})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    return data["user_id"], data["api_key"]


async def _create_conv(client: AsyncClient, api_key: str, title: str = "Test") -> str:
    """Create a conversation and return its id."""
    resp = await client.post(
        "/api/v1/conversations",
        json={"title": title},
        headers={"X-API-Key": api_key},
    )
    assert resp.status_code == 201, resp.text
    return resp.json()["id"]


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_health_ok(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/health")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert "application" in data
    assert "version" in data
    assert "timestamp" in data


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_register_creates_unique_api_keys(client: AsyncClient) -> None:
    """Two distinct registrations must produce two distinct API keys."""
    _, key1 = await _register(client, "Alice")
    _, key2 = await _register(client, "Bob")
    assert key1 != key2
    assert key1.startswith("ad_")
    assert key2.startswith("ad_")


@pytest.mark.asyncio
async def test_missing_api_key_returns_401(client: AsyncClient) -> None:
    resp = await client.get("/api/v1/conversations")
    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_invalid_api_key_returns_401(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/v1/conversations",
        headers={"X-API-Key": "ad_thisis_totally_invalid_key"},
    )
    assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Conversations
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_conversation_full_crud(client: AsyncClient, test_user: tuple[User, str]) -> None:
    _, raw_key = test_user
    headers = {"X-API-Key": raw_key}

    # Create
    create_resp = await client.post(
        "/api/v1/conversations", json={"title": "My Chat"}, headers=headers
    )
    assert create_resp.status_code == 201
    conv = create_resp.json()
    conv_id = conv["id"]
    assert conv["title"] == "My Chat"
    assert "created_at" in conv
    assert "updated_at" in conv

    # List — should have 1 conversation
    list_resp = await client.get("/api/v1/conversations", headers=headers)
    assert list_resp.status_code == 200
    body = list_resp.json()
    assert body["total"] == 1
    assert body["items"][0]["id"] == conv_id

    # Get single
    get_resp = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert get_resp.status_code == 200
    assert get_resp.json()["id"] == conv_id

    # Update title
    patch_resp = await client.patch(
        f"/api/v1/conversations/{conv_id}",
        json={"title": "Renamed Chat"},
        headers=headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["title"] == "Renamed Chat"

    # Delete
    del_resp = await client.delete(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify gone
    get_gone = await client.get(f"/api/v1/conversations/{conv_id}", headers=headers)
    assert get_gone.status_code == 404


@pytest.mark.asyncio
async def test_conversation_not_found_returns_404(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, raw_key = test_user
    fake_id = "00000000-0000-0000-0000-000000000001"
    resp = await client.get(
        f"/api/v1/conversations/{fake_id}",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cross_user_conversation_isolation(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, key1 = test_user
    _, key2 = await _register(client, "Eve")

    # User 1 creates a private conversation
    conv_id = await _create_conv(client, key1, "Private")

    # User 2 cannot see user 1's conversation
    resp = await client.get(
        f"/api/v1/conversations/{conv_id}", headers={"X-API-Key": key2}
    )
    assert resp.status_code == 404

    # User 2 cannot delete user 1's conversation
    resp = await client.delete(
        f"/api/v1/conversations/{conv_id}", headers={"X-API-Key": key2}
    )
    assert resp.status_code == 404

    # User 2 cannot update user 1's conversation
    resp = await client.patch(
        f"/api/v1/conversations/{conv_id}",
        json={"title": "Hacked"},
        headers={"X-API-Key": key2},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_conversations_only_own(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, key1 = test_user
    _, key2 = await _register(client, "Charlie")

    await _create_conv(client, key1, "Conv A")
    await _create_conv(client, key1, "Conv B")
    await _create_conv(client, key2, "Conv C")

    resp = await client.get("/api/v1/conversations", headers={"X-API-Key": key1})
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 2
    titles = {item["title"] for item in data["items"]}
    assert titles == {"Conv A", "Conv B"}


# ---------------------------------------------------------------------------
# Messages
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_list_messages_empty_conversation(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, raw_key = test_user
    conv_id = await _create_conv(client, raw_key, "Empty Conv")
    resp = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] == 0
    assert data["items"] == []


@pytest.mark.asyncio
async def test_list_messages_for_nonexistent_conversation(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, raw_key = test_user
    fake_id = "00000000-0000-0000-0000-000000000002"
    resp = await client.get(
        f"/api/v1/conversations/{fake_id}/messages",
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_send_message_returns_sse_stream(
    client: AsyncClient,
    test_user: tuple[User, str],
) -> None:
    """
    The POST /messages endpoint must return an SSE stream with at least
    one 'event: done' line and no 'event: error'.
    """
    _, raw_key = test_user
    conv_id = await _create_conv(client, raw_key, "SSE Test")

    resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Hello agent!"},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200
    assert "text/event-stream" in resp.headers.get("content-type", "")

    body = resp.text
    # Must have a done event
    assert "event: done" in body
    # Must not have an error event
    assert "event: error" not in body


@pytest.mark.asyncio
async def test_send_message_creates_history(
    client: AsyncClient,
    test_user: tuple[User, str],
) -> None:
    """After sending a message, the history should contain user + assistant messages."""
    _, raw_key = test_user
    conv_id = await _create_conv(client, raw_key, "History Test")
    headers = {"X-API-Key": raw_key}

    # Send a message (triggers SSE agent loop)
    await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "What is 2 + 2?"},
        headers=headers,
    )

    # Retrieve history
    history_resp = await client.get(
        f"/api/v1/conversations/{conv_id}/messages",
        headers=headers,
    )
    assert history_resp.status_code == 200
    data = history_resp.json()
    roles = [m["role"] for m in data["items"]]
    # At minimum: user message and an assistant reply
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_send_message_to_nonexistent_conv_returns_error(
    client: AsyncClient,
    test_user: tuple[User, str],
) -> None:
    """Sending a message to a missing conversation must return SSE error event."""
    _, raw_key = test_user
    fake_id = "00000000-0000-0000-0000-000000000003"
    resp = await client.post(
        f"/api/v1/conversations/{fake_id}/messages",
        json={"content": "Hello?"},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 200  # SSE always 200
    assert "event: error" in resp.text


@pytest.mark.asyncio
async def test_cross_user_cannot_send_message(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, key1 = test_user
    _, key2 = await _register(client, "Attacker")

    conv_id = await _create_conv(client, key1, "Owner Conv")

    resp = await client.post(
        f"/api/v1/conversations/{conv_id}/messages",
        json={"content": "Intruder message"},
        headers={"X-API-Key": key2},
    )
    # SSE response with error event (conversation not found for user2)
    assert resp.status_code == 200
    assert "event: error" in resp.text


# ---------------------------------------------------------------------------
# Tasks
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_task_full_crud(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, raw_key = test_user
    headers = {"X-API-Key": raw_key}

    # Create
    create_resp = await client.post(
        "/api/v1/tasks", json={"title": "Buy milk"}, headers=headers
    )
    assert create_resp.status_code == 201
    task = create_resp.json()
    task_id = task["id"]
    assert task["title"] == "Buy milk"
    assert task["is_done"] is False

    # List
    list_resp = await client.get("/api/v1/tasks", headers=headers)
    assert list_resp.status_code == 200
    assert list_resp.json()["total"] == 1

    # Patch — mark done
    patch_resp = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"is_done": True}, headers=headers
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["is_done"] is True

    # Patch — rename
    rename_resp = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"title": "Buy oat milk"}, headers=headers
    )
    assert rename_resp.status_code == 200
    assert rename_resp.json()["title"] == "Buy oat milk"

    # Delete
    del_resp = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert del_resp.status_code == 204

    # Verify gone
    patch_gone = await client.patch(
        f"/api/v1/tasks/{task_id}", json={"is_done": False}, headers=headers
    )
    assert patch_gone.status_code == 404


@pytest.mark.asyncio
async def test_task_filter_by_is_done(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, raw_key = test_user
    headers = {"X-API-Key": raw_key}

    # Create two tasks
    r1 = await client.post("/api/v1/tasks", json={"title": "Open task"}, headers=headers)
    r2 = await client.post("/api/v1/tasks", json={"title": "Done task"}, headers=headers)
    assert r1.status_code == 201
    assert r2.status_code == 201
    task2_id = r2.json()["id"]

    # Mark second task done
    await client.patch(f"/api/v1/tasks/{task2_id}", json={"is_done": True}, headers=headers)

    # Filter open tasks
    open_resp = await client.get("/api/v1/tasks?is_done=false", headers=headers)
    assert open_resp.status_code == 200
    open_data = open_resp.json()
    assert open_data["total"] == 1
    assert open_data["items"][0]["title"] == "Open task"

    # Filter done tasks
    done_resp = await client.get("/api/v1/tasks?is_done=true", headers=headers)
    assert done_resp.status_code == 200
    done_data = done_resp.json()
    assert done_data["total"] == 1
    assert done_data["items"][0]["title"] == "Done task"


@pytest.mark.asyncio
async def test_cross_user_task_isolation(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, key1 = test_user
    _, key2 = await _register(client, "Thief")

    # User 1 creates a task
    create_resp = await client.post(
        "/api/v1/tasks", json={"title": "Secret task"}, headers={"X-API-Key": key1}
    )
    task_id = create_resp.json()["id"]

    # User 2 cannot read user 1's tasks in their list
    list_resp = await client.get("/api/v1/tasks", headers={"X-API-Key": key2})
    assert list_resp.json()["total"] == 0

    # User 2 cannot patch user 1's task
    patch_resp = await client.patch(
        f"/api/v1/tasks/{task_id}",
        json={"is_done": True},
        headers={"X-API-Key": key2},
    )
    assert patch_resp.status_code == 404

    # User 2 cannot delete user 1's task
    del_resp = await client.delete(
        f"/api/v1/tasks/{task_id}", headers={"X-API-Key": key2}
    )
    assert del_resp.status_code == 404


@pytest.mark.asyncio
async def test_task_not_found_returns_404(
    client: AsyncClient, test_user: tuple[User, str]
) -> None:
    _, raw_key = test_user
    fake_id = "00000000-0000-0000-0000-000000000004"
    resp = await client.patch(
        f"/api/v1/tasks/{fake_id}",
        json={"is_done": True},
        headers={"X-API-Key": raw_key},
    )
    assert resp.status_code == 404
