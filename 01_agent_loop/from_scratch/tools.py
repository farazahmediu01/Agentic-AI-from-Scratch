"""
Step 1 — Tools available to the agent.

The tools are deliberately trivial. The interesting behavior is NOT the
tool implementations — it's the agent's decision to pick the right tool
and chain results across turns.

Each tool here is paired with a JSON schema that describes its name,
purpose, and arguments. The model uses the schema to decide *whether*
and *how* to call the tool. We use the schema to decide *what* to dispatch
when a tool call arrives back.
"""

from datetime import datetime
from typing import Callable

from openai.types.chat import ChatCompletionToolParam


# -----------------------------------------------------------------------------
# Tool implementations (plain Python functions — nothing agent-specific here)
# -----------------------------------------------------------------------------


def get_current_time() -> str:
    """Return the current local time as an ISO 8601 string (seconds precision)."""
    return datetime.now().isoformat(timespec="seconds")


def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Return the product of two numbers."""
    return a * b


def divide(a: float, b: float) -> float:
    """Return the division of two numbers."""
    return a / b


def subtract(a: float, b: float) -> float:
    """Return the subtraction of two numbers."""
    return a - b


# -----------------------------------------------------------------------------
# Registry: maps tool name (string the model emits) -> callable to dispatch.
# This is the bridge between "the model said the word 'add'" and "actually run add()."
# -----------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, Callable] = {
    "get_current_time": get_current_time,
    "add": add,
    "multiply": multiply,
    "subtract": subtract,
    "divide": divide,
}


# -----------------------------------------------------------------------------
# Tool schemas in OpenAI Chat Completions tool-calling format.
#
# Each entry tells the model: here is a tool you may call, here is what it
# does, and here are the exact arguments it expects. The model never sees
# the Python functions — only these schemas.
# -----------------------------------------------------------------------------

TOOL_SCHEMAS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local time as an ISO 8601 timestamp. Takes no arguments.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two numbers and return their sum.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "multiply",
            "description": "Multiply two numbers and return their product.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "divide",
            "description": "Divide two numbers and return their quotient.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "subtract",
            "description": "Subtract two numbers and return their difference.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First number"},
                    "b": {"type": "number", "description": "Second number"},
                },
                "required": ["a", "b"],
            },
        },
    },
]
