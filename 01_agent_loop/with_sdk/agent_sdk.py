"""
Step 1, Layer 4 — the SAME agent, rebuilt with the OpenAI Agents SDK.

Compare this file with `../from_scratch/agent.py` + `../from_scratch/tools.py`.
Same behaviour. Same tools. Same task. About one fifth of the code.

Nothing here is magic to you any more. Every line maps to something you already
built by hand — `compare.md` in this folder draws the map line by line.

Run:  uv run python 01_agent_loop/with_sdk/agent_sdk.py
"""

from __future__ import annotations

import asyncio
from datetime import datetime

from agents import Agent, Runner, function_tool

from shared.models import make_model

# One line, and the SDK is pointed at Gemini's OpenAI-compatible endpoint — the
# same base_url trick you used from scratch. The SDK does not care which provider
# is behind it.
#
# `make_model()` reads AGENT_PROVIDER from .env and hands back either a
# Chat Completions model (Gemini, free — the default) or a Responses model
# (OpenAI, paid). Open `shared/models.py` and read it: it is 40 lines, and it is
# the seam that lets the late hosted-tools chapter run without editing this file.
MODEL = make_model()


# -----------------------------------------------------------------------------
# Tools.
#
# Look at what disappeared: TOOL_SCHEMAS is gone. All 60 lines of hand-written
# JSON Schema are now generated from the type hints and the docstring. The
# docstring IS the description the model reads — which is why Practice 5's
# lesson still applies, it just moved location.
# -----------------------------------------------------------------------------


@function_tool
def get_current_time() -> str:
    """Get the current local time as an ISO 8601 timestamp."""
    return datetime.now().isoformat(timespec="seconds")


@function_tool
def add(a: float, b: float) -> float:
    """Add two numbers and return their sum."""
    return a + b


@function_tool
def multiply(a: float, b: float) -> float:
    """Multiply two numbers and return their product."""
    return a * b


@function_tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the difference."""
    return a - b


@function_tool
def divide(a: float, b: float) -> float:
    """Divide a by b and return the quotient."""
    return a / b


# -----------------------------------------------------------------------------
# The agent.
#
# TOOL_REGISTRY is gone too — passing the functions in `tools=` registers them.
# `instructions` is your `system_prompt`. That is the whole setup.
# -----------------------------------------------------------------------------

agent = Agent(
    name="Calculator Agent",
    instructions=(
        "You are a careful assistant. Use the available tools to answer the "
        "user's question step by step. Chain tool calls when one result feeds "
        "the next. When you have everything you need, stop calling tools and "
        "write a clean final summary."
    ),
    model=MODEL,
    tools=[get_current_time, add, multiply, subtract, divide],
)


async def main() -> None:
    task = (
        "What's the current time? Also, calculate 15 multiplied by 7, "
        "then add 23 to that result. Give me a single clean summary at the end."
    )

    print(f"USER TASK:\n  {task}")
    print("=" * 72)

    # `Runner.run` IS your for-loop. `max_turns` IS your MAX_ITERATIONS.
    result = await Runner.run(agent, task, max_turns=10)

    # The loop you wrote printed each tool call as it happened. The SDK collected
    # them instead — same information, retrieved after the fact.
    from agents.items import ToolCallItem

    tool_calls = [item for item in result.new_items if isinstance(item, ToolCallItem)]
    print(f"\nThe SDK ran {len(tool_calls)} tool call(s) inside Runner.run():")
    for item in tool_calls:
        raw = item.raw_item
        name = getattr(raw, "name", "?")
        args = getattr(raw, "arguments", "")
        print(f"  -> {name}({args})")

    print("=" * 72)
    print(f"\nFINAL ANSWER:\n{result.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())
