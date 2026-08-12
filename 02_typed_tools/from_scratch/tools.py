"""
Chapter 2 — the same tools as Chapter 1, now under contract.

Open `../../01_agent_loop/from_scratch/tools.py` next to this file. Same five
calculator tools. That file is 145 lines; roughly 90 of them are hand-written
JSON Schema. This file has none, because `@tool` generates it from what you see.

Three things to notice, in order of importance:

  1. `Literal[...]` on `unit` is a CLOSED SET. Chapter 1 could only ask for one
     politely, in English, inside a "description". Here it is enforced before
     the function body runs — the model physically cannot get an invalid unit
     past the boundary.
  2. `Annotated[float, Field(ge=0, le=100)]` puts a RANGE in the type. It shows
     up in the schema the model reads AND in the check on the way back in.
  3. `divide` still raises by hand. Not every rule fits in a type — "b must not
     be zero" is a relationship between arguments, not a property of one. Know
     which rules the type system can hold and which you still owe by hand.
"""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import Field

from typed_tool import Tool, ToolError, tool


@tool
def get_current_time() -> str:
    """Get the current local time as an ISO 8601 timestamp. Takes no arguments."""
    return datetime.now().isoformat(timespec="seconds")


@tool
def add(a: float, b: float) -> float:
    """Add two numbers and return their sum."""
    return a + b


@tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return their product."""
    return a * b


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the difference."""
    return a - b


@tool
def divide(a: float, b: float) -> float:
    """Divide a by b and return the quotient."""
    # The type system cannot express "b is any float except zero", so this guard
    # stays hand-written. It raises ToolError rather than ZeroDivisionError
    # because the model is the one who can fix it — by not dividing by zero.
    if b == 0:
        raise ToolError(
            "Cannot divide by zero. Check the value you passed as 'b' and, if it "
            "genuinely is zero, explain to the user that the result is undefined."
        )
    return a / b


@tool
def convert_temperature(
    value: float,
    from_unit: Literal["celsius", "fahrenheit", "kelvin"],
    to_unit: Literal["celsius", "fahrenheit", "kelvin"],
) -> float:
    """
    Convert a temperature between celsius, fahrenheit and kelvin.

    Use the exact unit names listed — they are the only ones accepted.
    """
    to_celsius = {
        "celsius": lambda v: v,
        "fahrenheit": lambda v: (v - 32) * 5 / 9,
        "kelvin": lambda v: v - 273.15,
    }
    from_celsius = {
        "celsius": lambda c: c,
        "fahrenheit": lambda c: c * 9 / 5 + 32,
        "kelvin": lambda c: c + 273.15,
    }
    return round(from_celsius[to_unit](to_celsius[from_unit](value)), 4)


@tool
def percentage_of(
    value: float,
    percent: Annotated[float, Field(ge=0, le=100, description="A percentage from 0 to 100")],
) -> float:
    """Return `percent` percent of `value`. Use it for discounts and tax."""
    return value * percent / 100


# One list, and everything the loop needs is derived from it.
ALL_TOOLS: list[Tool] = [
    get_current_time,
    add,
    multiply,
    subtract,
    divide,
    convert_temperature,
    percentage_of,
]
