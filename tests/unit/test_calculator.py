"""
Extended unit tests for the calculator tool.
Tests pure math, math functions, constants, error cases, and injection prevention.
"""

import pytest
from app.tools.calculator import calculate


@pytest.mark.asyncio
async def test_calculate_addition():
    assert (await calculate("2 + 2"))["result"] == 4


@pytest.mark.asyncio
async def test_calculate_subtraction():
    assert (await calculate("10 - 3"))["result"] == 7


@pytest.mark.asyncio
async def test_calculate_multiplication():
    assert (await calculate("6 * 7"))["result"] == 42


@pytest.mark.asyncio
async def test_calculate_division():
    res = await calculate("22 / 7")
    assert abs(res["result"] - 3.142857) < 0.001


@pytest.mark.asyncio
async def test_calculate_floor_division():
    assert (await calculate("22 // 7"))["result"] == 3


@pytest.mark.asyncio
async def test_calculate_modulo():
    assert (await calculate("17 % 5"))["result"] == 2


@pytest.mark.asyncio
async def test_calculate_exponentiation():
    assert (await calculate("2 ** 10"))["result"] == 1024


@pytest.mark.asyncio
async def test_calculate_sqrt():
    assert (await calculate("sqrt(144)"))["result"] == 12.0


@pytest.mark.asyncio
async def test_calculate_nested_expression():
    res = await calculate("sqrt(16) * 5 + 3")
    assert res["result"] == 23.0


@pytest.mark.asyncio
async def test_calculate_pi_constant():
    import math
    res = await calculate("pi * 2")
    assert abs(res["result"] - 2 * math.pi) < 1e-9


@pytest.mark.asyncio
async def test_calculate_e_constant():
    import math
    res = await calculate("e")
    assert abs(res["result"] - math.e) < 1e-9


@pytest.mark.asyncio
async def test_calculate_unary_negation():
    assert (await calculate("-5 + 10"))["result"] == 5


@pytest.mark.asyncio
async def test_calculate_percent_to_decimal():
    """Tax calculation pattern: price * 1.08"""
    res = await calculate("100 * 1.08")
    assert abs(res["result"] - 108.0) < 1e-9


@pytest.mark.asyncio
async def test_calculate_import_blocked():
    """Injection: import statement must return an error, not execute."""
    res = await calculate("import os")
    assert "error" in res
    assert "result" not in res


@pytest.mark.asyncio
async def test_calculate_exec_blocked():
    res = await calculate("exec('print(1)')")
    assert "error" in res


@pytest.mark.asyncio
async def test_calculate_unknown_name_blocked():
    res = await calculate("secret_var + 1")
    assert "error" in res


@pytest.mark.asyncio
async def test_calculate_empty_expression_error():
    res = await calculate("")
    assert "error" in res


@pytest.mark.asyncio
async def test_calculate_division_by_zero_error():
    res = await calculate("1 / 0")
    assert "error" in res


@pytest.mark.asyncio
async def test_calculate_returns_expression_in_result():
    """Response must always echo the input expression."""
    expr = "3 * 3"
    res = await calculate(expr)
    assert res["expression"] == expr
