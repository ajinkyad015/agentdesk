from __future__ import annotations

import ast
import math
import operator
from typing import Any

# Allowed operators
OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

# Allowed math functions
FUNCTIONS = {
    "abs": abs,
    "round": round,
    "sqrt": math.sqrt,
    "sin": math.sin,
    "cos": math.cos,
    "tan": math.tan,
    "log": math.log,
    "log10": math.log10,
    "exp": math.exp,
    "ceil": math.ceil,
    "floor": math.floor,
}

# Allowed constants
CONSTANTS = {
    "pi": math.pi,
    "e": math.e,
}


def _eval_ast(node: ast.AST) -> float | int:
    if isinstance(node, ast.Expression):
        return _eval_ast(node.body)

    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    elif isinstance(node, ast.Name):
        if node.id in CONSTANTS:
            return CONSTANTS[node.id]
        raise ValueError(f"Unknown variable or constant '{node.id}'")

    elif isinstance(node, ast.UnaryOp):
        op_type = type(node.op)
        if op_type in OPERATORS:
            operand = _eval_ast(node.operand)
            return OPERATORS[op_type](operand)
        raise ValueError(f"Unsupported unary operator {op_type.__name__}")

    elif isinstance(node, ast.BinOp):
        op_type = type(node.op)
        if op_type in OPERATORS:
            left = _eval_ast(node.left)
            right = _eval_ast(node.right)
            return OPERATORS[op_type](left, right)
        raise ValueError(f"Unsupported binary operator {op_type.__name__}")

    elif isinstance(node, ast.Call):
        if isinstance(node.func, ast.Name) and node.func.id in FUNCTIONS:
            func = FUNCTIONS[node.func.id]
            args = [_eval_ast(arg) for arg in node.args]
            return func(*args)
        raise ValueError("Unsupported or unknown function call")

    else:
        raise ValueError(f"Unsupported syntax: {type(node).__name__}")


async def calculate(expression: str) -> dict[str, Any]:
    """
    Safely evaluate a mathematical expression without using eval().
    """
    try:
        parsed = ast.parse(expression.strip(), mode="eval")
        result = _eval_ast(parsed)
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"expression": expression, "error": str(e)}
