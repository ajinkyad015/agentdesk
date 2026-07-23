import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={"display_name": "Alice"})
    assert response.status_code == 201
    data = response.json()
    assert "api_key" in data
    assert "user_id" in data
    assert data["api_key"].startswith("ad_")
