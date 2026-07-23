from __future__ import annotations

from typing import Any, Callable
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession

from app.tools.calculator import calculate
from app.tools.weather import get_weather
from app.tools import tasks_tool

# JSON Schemas for OpenAI / Anthropic function calling
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "calculate",
            "description": "Safely evaluate a mathematical expression (e.g. 2 + 2, sqrt(16), 15 * 1.08).",
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "The math expression to evaluate.",
                    }
                },
                "required": ["expression"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get current weather for a city/location or latitude/longitude.",
            "parameters": {
                "type": "object",
                "properties": {
                    "location": {
                        "type": "string",
                        "description": "City name or location (e.g. 'London', 'Pune', 'New York').",
                    },
                    "latitude": {"type": "number", "description": "Latitude coordinate."},
                    "longitude": {"type": "number", "description": "Longitude coordinate."},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_task",
            "description": "Create a new to-do task for the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Title or summary of the task.",
                    }
                },
                "required": ["title"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_tasks",
            "description": "List the user's tasks. Optionally filter by status.",
            "parameters": {
                "type": "object",
                "properties": {
                    "is_done": {
                        "type": "boolean",
                        "description": "Filter by completed status: true for done, false for open tasks.",
                    }
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "complete_task",
            "description": "Mark a specific task as completed using its task ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "task_id": {
                        "type": "string",
                        "description": "UUID string of the task to complete.",
                    }
                },
                "required": ["task_id"],
            },
        },
    },
]


class ToolRegistry:
    """
    Registry for resolving and executing tool calls.
    """

    def __init__(self, db: AsyncSession | None = None, user_id: UUID | None = None):
        self.db = db
        self.user_id = user_id

    def get_schemas(self) -> list[dict[str, Any]]:
        return TOOL_SCHEMAS

    async def execute_tool(self, name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        """
        Execute a tool by name with arguments.
        """
        if name == "calculate":
            expr = str(arguments.get("expression", ""))
            return await calculate(expr)

        elif name == "get_weather":
            loc = arguments.get("location")
            lat = arguments.get("latitude")
            lon = arguments.get("longitude")
            return await get_weather(location=loc, latitude=lat, longitude=lon)

        elif name == "create_task":
            if self.db is None or self.user_id is None:
                return {"error": "Database session / user context missing"}
            title = str(arguments.get("title", ""))
            return await tasks_tool.create_task(self.db, self.user_id, title)

        elif name == "list_tasks":
            if self.db is None or self.user_id is None:
                return {"error": "Database session / user context missing"}
            is_done = arguments.get("is_done")
            return await tasks_tool.list_tasks(self.db, self.user_id, is_done)

        elif name == "complete_task":
            if self.db is None or self.user_id is None:
                return {"error": "Database session / user context missing"}
            task_id = str(arguments.get("task_id", ""))
            return await tasks_tool.complete_task(self.db, self.user_id, task_id)

        else:
            return {"error": f"Unknown tool name '{name}'"}
