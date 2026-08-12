"""
Chapter 2, Layer 4 -- the same typed tools, on the OpenAI Agents SDK.

    uv run python 02_typed_tools/with_sdk/agent_sdk.py

You just wrote `typed_tool.py`. `@function_tool` is that file. Same three moves
-- read the signature, build a Pydantic validator, generate the JSON Schema --
and it reaches the same conclusions, including `additionalProperties: false`.

So this file is short. What is worth your attention is not what the SDK does
the same, it is the ONE decision it makes differently, and it is a decision
about error text. Run the file: the second half deliberately fails a tool call
and prints what the model would have been told, first by the SDK's default and
then by ours.

`compare.md` in this folder has the full map.
"""

from __future__ import annotations

import asyncio
from datetime import datetime
from typing import Annotated, Any, Literal

from agents import (
    Agent,
    RunContextWrapper,
    Runner,
    _debug,
    function_tool,
)
from agents.exceptions import ModelBehaviorError
from agents.tool_context import ToolContext
from pydantic import Field, ValidationError

from shared.models import make_model

MODEL = make_model()


# -----------------------------------------------------------------------------
# Error text: the one place the SDK's default is worse than yours, and the
# reason is more interesting than "they forgot".
#
# Out of the box, a rejected tool call reaches the model as exactly this:
#
#     "Invalid JSON input for tool add."
#
# One sentence. Not which argument. Not what type it wanted. Not what you sent.
# Compare it with what `explain()` produced from the same failure in
# `../from_scratch/typed_tool.py` and ask how a model is supposed to recover.
#
# It is not an oversight. The SDK ships with `OPENAI_AGENTS_DONT_LOG_TOOL_DATA`
# defaulting to ON, because tool arguments routinely contain personal data --
# amounts, emails, addresses -- and echoing them into logs and traces by default
# would be a privacy incident waiting for a customer. So the SDK chose privacy
# over recoverability, and it chose on YOUR behalf.
#
# That is the actual lesson of this chapter's SDK layer. A framework's defaults
# encode somebody else's judgement about your tradeoffs. Knowing the mechanism
# is what lets you notice you disagree.
#
# `failure_error_function` is the hook that hands the decision back. It is the
# direct equivalent of our `explain()`, and it is a per-tool argument -- so you
# can be verbose for `add` and silent for `charge_credit_card`.
# -----------------------------------------------------------------------------


def explain_to_model(ctx: RunContextWrapper[Any], error: Exception) -> str:
    """Rewrite a tool failure as an instruction the model can act on."""
    tool_name = ctx.tool_name if isinstance(ctx, ToolContext) else "the tool"

    # The SDK wraps argument-validation failures in ModelBehaviorError. Its
    # __cause__ is the original Pydantic ValidationError, which is where the
    # per-field detail lives.
    cause = error.__cause__
    if isinstance(error, ModelBehaviorError) and isinstance(cause, ValidationError):
        lines = [
            f"  - {'.'.join(str(p) for p in e['loc']) or '(whole object)'}: "
            f"{e['msg']} (you sent: {e.get('input')!r})"
            for e in cause.errors()
        ]
        return (
            f"INVALID ARGUMENTS for tool '{tool_name}'. Nothing was executed.\n"
            + "\n".join(lines)
            + f"\nFix the arguments and call '{tool_name}' again. If the correct value "
            f"is something the user never told you, ask them for it. Do not invent it."
        )

    return (
        f"The tool '{tool_name}' failed: {error}. If this is not something you can "
        f"fix by changing the arguments, tell the user and stop retrying."
    )


# -----------------------------------------------------------------------------
# The tools. Compare with `../from_scratch/tools.py` -- the bodies are identical
# and the signatures are identical. Only the decorator changed.
# -----------------------------------------------------------------------------


@function_tool(failure_error_function=explain_to_model)
def get_current_time() -> str:
    """Get the current local time as an ISO 8601 timestamp. Takes no arguments."""
    return datetime.now().isoformat(timespec="seconds")


@function_tool(failure_error_function=explain_to_model)
def add(a: float, b: float) -> float:
    """Add two numbers and return their sum."""
    return a + b


@function_tool(failure_error_function=explain_to_model)
def subtract(a: float, b: float) -> float:
    """Subtract b from a and return the difference."""
    return a - b


@function_tool(failure_error_function=explain_to_model)
def divide(a: float, b: float) -> float:
    """Divide a by b and return the quotient."""
    # Still hand-written, for the same reason as in the from-scratch build: the
    # rule is about a relationship, not a type. Raising here is correct -- the
    # SDK routes it through `failure_error_function` just like a bad argument.
    if b == 0:
        raise ValueError(
            "Cannot divide by zero. If the divisor genuinely is zero, explain to "
            "the user that the result is undefined."
        )
    return a / b


@function_tool(failure_error_function=explain_to_model)
def convert_temperature(
    value: float,
    from_unit: Literal["celsius", "fahrenheit", "kelvin"],
    to_unit: Literal["celsius", "fahrenheit", "kelvin"],
) -> float:
    """
    Convert a temperature between celsius, fahrenheit and kelvin.

    Use the exact unit names listed -- they are the only ones accepted.
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


@function_tool(failure_error_function=explain_to_model)
def percentage_of(
    value: float,
    percent: Annotated[float, Field(ge=0, le=100, description="A percentage from 0 to 100")],
) -> float:
    """Return `percent` percent of `value`. Use it for discounts and tax."""
    return value * percent / 100


agent = Agent(
    name="Typed Calculator",
    instructions=(
        "You are a careful assistant. Use the available tools to answer the "
        "user's question step by step. If a tool rejects your arguments, read "
        "the error, fix the arguments, and try once more. Never invent values "
        "the user did not give you. When you have everything you need, stop "
        "calling tools and write a clean final summary."
    ),
    model=MODEL,
    tools=[get_current_time, add, subtract, divide, convert_temperature, percentage_of],
)


async def show_generated_schema() -> None:
    """The schema the SDK built, next to the one you built."""
    import json

    print("SCHEMA GENERATED BY @function_tool (convert_temperature):")
    print(json.dumps(convert_temperature.params_json_schema, indent=2))
    print(f"\nstrict_json_schema = {convert_temperature.strict_json_schema}")
    print(
        "\n`strict_json_schema=True` is the SDK asking the PROVIDER to constrain\n"
        "generation to this schema, so many invalid calls are never emitted at\n"
        "all. That is a layer you did not build and cannot build -- it lives in\n"
        "the model server. It is also not universal: not every provider honours\n"
        "it, which is exactly why the validation you wrote still has to exist."
    )


async def show_rejected_call() -> None:
    """Invoke a tool directly with arguments no sane model should send."""
    bad_args = '{"a": "fifty", "b": 3}'
    ctx: ToolContext[Any] = ToolContext(
        context=None,
        tool_name="add",
        tool_call_id="demo-1",
        tool_arguments=bad_args,
    )

    print("\n" + "=" * 72)
    print(f"A REJECTED CALL: add({bad_args})\n")

    print("--- what the model receives with the SDK's default privacy setting ---")
    print(await add.on_invoke_tool(ctx, bad_args))

    # Flip the privacy flag and run the identical call again. In a real project
    # you set OPENAI_AGENTS_DONT_LOG_TOOL_DATA=0 in the environment; we poke the
    # module here so the two outputs sit next to each other on your screen.
    _debug.DONT_LOG_TOOL_DATA = False
    print("\n--- the same failure with OPENAI_AGENTS_DONT_LOG_TOOL_DATA=0 ---")
    print(await add.on_invoke_tool(ctx, bad_args))
    _debug.DONT_LOG_TOOL_DATA = True

    print(
        "\nSame rejection, two different amounts of help. The first is unusable:\n"
        "a model told only 'invalid input' has nothing to change, so it retries\n"
        "the identical call, burns your turn budget, and eventually apologises\n"
        "to the user for a problem it was never shown.\n"
        "\n"
        "Note also what did NOT happen in either case: `add` never ran. The SDK\n"
        "validated first, exactly as `Tool.call` does, so a rejected call has no\n"
        "side effects. The run is still alive and the model gets another turn --\n"
        "the failure is data in the conversation, not a crash."
    )


async def main() -> None:
    await show_generated_schema()
    await show_rejected_call()

    task = (
        "Convert 98.6 fahrenheit to celsius, then tell me what 15% of that "
        "number is. Finish with one clean sentence."
    )
    print("\n" + "=" * 72)
    print(f"USER TASK:\n  {task}")

    result = await Runner.run(agent, task, max_turns=10)

    from agents.items import ToolCallItem

    print("\nTool calls the SDK made:")
    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            raw = item.raw_item
            print(f"  -> {getattr(raw, 'name', '?')}({getattr(raw, 'arguments', '')})")

    print(f"\nFINAL ANSWER:\n{result.final_output}\n")


if __name__ == "__main__":
    asyncio.run(main())
