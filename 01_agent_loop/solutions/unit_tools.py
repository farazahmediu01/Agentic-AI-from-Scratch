"""Exercise 4 solution — tools for the Unit Converter Agent."""

from __future__ import annotations

from typing import Callable

from openai.types.chat import ChatCompletionToolParam


def celsius_to_fahrenheit(celsius: float) -> float:
    """Convert Celsius to Fahrenheit."""
    return celsius * 9 / 5 + 32


def km_to_miles(km: float) -> float:
    """Convert kilometres to miles."""
    return km * 0.621371


def kg_to_pounds(kg: float) -> float:
    """Convert kilograms to pounds."""
    return kg * 2.20462


def round_number(value: float, decimals: int) -> float:
    """Round a number to a given number of decimal places."""
    return round(value, decimals)


# Design answer (the exercise asks you to decide and justify):
# `round_number` stays a separate tool here *for teaching reasons* — it forces a
# visible second hop where one tool consumes another tool's output. In production
# you would round inside each converter: an extra round-trip to the model per
# value costs latency and tokens to do something Python already did for free.
# Rule of thumb: a tool should exist when the *model* needs to decide whether to
# use it, not when your code merely needs the operation performed.

TOOL_REGISTRY: dict[str, Callable] = {
    "celsius_to_fahrenheit": celsius_to_fahrenheit,
    "km_to_miles": km_to_miles,
    "kg_to_pounds": kg_to_pounds,
    "round_number": round_number,
}


TOOL_SCHEMAS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "celsius_to_fahrenheit",
            "description": "Convert a temperature from degrees Celsius to degrees Fahrenheit.",
            "parameters": {
                "type": "object",
                "properties": {
                    "celsius": {"type": "number", "description": "Temperature in Celsius"},
                },
                "required": ["celsius"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "km_to_miles",
            "description": "Convert a distance from kilometres to miles.",
            "parameters": {
                "type": "object",
                "properties": {
                    "km": {"type": "number", "description": "Distance in kilometres"},
                },
                "required": ["km"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "kg_to_pounds",
            "description": "Convert a mass from kilograms to pounds.",
            "parameters": {
                "type": "object",
                "properties": {
                    "kg": {"type": "number", "description": "Mass in kilograms"},
                },
                "required": ["kg"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "round_number",
            "description": (
                "Round a number to a given number of decimal places. Use this on the "
                "output of a conversion tool when the user asks for a specific precision."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "value": {"type": "number", "description": "The number to round"},
                    "decimals": {
                        "type": "integer",
                        "description": "How many decimal places to keep",
                    },
                },
                "required": ["value", "decimals"],
            },
        },
    },
]
