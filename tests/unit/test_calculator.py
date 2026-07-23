import pytest
from app.tools.calculator import calculate


@pytest.mark.asyncio
async def test_calculate_basic():
    res = await calculate("2 + 2")
    assert res.get("result") == 4


@pytest.mark.asyncio
async def test_calculate_complex():
    res = await calculate("sqrt(16) * 5 + 3")
    assert res.get("result") == 23


@pytest.mark.asyncio
async def test_calculate_error():
    res = await calculate("import os")
    assert "error" in res
