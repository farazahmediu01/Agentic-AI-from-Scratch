"""
Spendly Lite v2 — SDK build (Layer 4 + 6).

    uv run python 02_typed_tools/solutions/expense_agent_sdk.py

Same seven tools, same system prompt, same storage, same golden dataset. The
business logic is imported from `expense_tools` and called through `.fn` — the
plain function inside our `Tool` — so the two builds cannot quietly diverge.

The interesting line in this file is `failure_error_function=explain_to_model`.
Everything else is a straight swap: `@tool` becomes `@function_tool`, our loop
becomes `Runner.run`, our `Tool.call` boundary becomes the SDK's. The error text
is the one place where the default is a decision you should override, and the
one place where the code you wrote in `typed_tool.py` is measurably better than
what the framework ships.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from agents import Agent, Runner, function_tool
from agents.exceptions import ModelBehaviorError
from agents.items import ToolCallItem, ToolCallOutputItem
from agents.run_context import RunContextWrapper
from agents.tool_context import ToolContext
from pydantic import ValidationError

import expense_tools as t
from expense_agent import SYSTEM_PROMPT, TASK
from expense_store import Category
from expense_tools import Amount, IsoDate, Limit, Month, Vendor
from shared.models import make_model

MODEL = make_model()

# The marker our error text starts with. The harness uses it to tell a rejected
# call apart from an executed one, which the SDK does not report directly.
REJECTED_PREFIX = "INVALID ARGUMENTS"


def explain_to_model(ctx: RunContextWrapper[Any], error: Exception) -> str:
    """The SDK equivalent of `typed_tool.explain()`."""
    tool_name = ctx.tool_name if isinstance(ctx, ToolContext) else "the tool"
    cause = error.__cause__

    if isinstance(error, ModelBehaviorError) and isinstance(cause, ValidationError):
        lines = [
            f"  - {'.'.join(str(p) for p in e['loc']) or '(whole object)'}: "
            f"{e['msg']} (you sent: {e.get('input')!r})"
            for e in cause.errors()
        ]
        return (
            f"{REJECTED_PREFIX} for tool '{tool_name}'. Nothing was executed.\n"
            + "\n".join(lines)
            + f"\nFix the arguments and call '{tool_name}' again. If the correct value "
            f"is something the user never told you, ask them for it. Do not invent it."
        )

    # Argument validation is not the only way a call fails. A business rule
    # raised from inside the body (`log_expense` on a future date) lands here,
    # and it is equally recoverable, so it keeps the same prefix.
    return f"{REJECTED_PREFIX} for tool '{tool_name}'. Nothing was executed.\n  - {error}"


# -----------------------------------------------------------------------------
# The same seven tools. Identical signatures to `expense_tools.py` — the SAME
# `Annotated` aliases are imported and reused, so there is genuinely one
# definition of what an Amount is across both builds.
# -----------------------------------------------------------------------------


@function_tool(failure_error_function=explain_to_model)
def get_today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return t.get_today.fn()


@function_tool(failure_error_function=explain_to_model)
def log_expense(
    vendor: Vendor,
    amount: Amount,
    category: Category,
    expense_date: IsoDate = "",
) -> str:
    """
    Record one expense in the user's ledger.

    This is the only tool here that changes anything. Call it only when the
    vendor, the amount and the category are all known. Never guess a value the
    user did not give you.
    """
    return t.log_expense.fn(vendor, amount, category, expense_date)


@function_tool(failure_error_function=explain_to_model)
def month_total(category: Category, month: Month = "") -> float:
    """
    Total amount already spent in one category during one month.

    Use it to answer "how much have I spent on X" and to check budgets.
    """
    return t.month_total.fn(category, month)


@function_tool(failure_error_function=explain_to_model)
def get_budget(category: Category) -> float:
    """Get the monthly budget in PKR for one category."""
    return t.get_budget.fn(category)


@function_tool(failure_error_function=explain_to_model)
def subtract(a: float, b: float) -> float:
    """Subtract b from a. Use it to compute budget remaining: subtract(budget, spent)."""
    return t.subtract.fn(a, b)


@function_tool(failure_error_function=explain_to_model)
def list_recent(limit: Limit = 5) -> str:
    """List the most recently recorded expenses, newest last."""
    return t.list_recent.fn(limit)


@function_tool(failure_error_function=explain_to_model)
def list_categories() -> str:
    """
    List every valid expense category.

    Call it when you need to TELL the user what the real options are.
    """
    return t.list_categories.fn()


agent = Agent(
    name="Spendly Lite v2",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    tools=[
        get_today,
        log_expense,
        month_total,
        get_budget,
        subtract,
        list_recent,
        list_categories,
    ],
)


# -----------------------------------------------------------------------------
# Adapter: make an SDK result look like our AgentRun.
#
# One property is new in Chapter 2 and it is the awkward one: `executed_names`.
# Our loop knows which calls were rejected because it caught the ToolError. The
# SDK swallows the failure and returns our error STRING as the tool output, so
# the only way back to the fact is to recognise the string we wrote.
#
# That is a genuine cost of the framework, and worth naming rather than hiding:
# an abstraction that handles an event for you also decides how much of that
# event you are allowed to see afterwards.
# -----------------------------------------------------------------------------


@dataclass
class SdkRun:
    final_answer: str
    iterations: int = 0
    tool_names: list[str] = field(default_factory=list)
    executed_names: list[str] = field(default_factory=list)
    hit_max_iterations: bool = False
    tool_arguments: list[tuple[str, str]] = field(default_factory=list)

    @property
    def rejected_count(self) -> int:
        return len(self.tool_names) - len(self.executed_names)


async def run_expense_agent(prompt: str, max_turns: int = 15) -> SdkRun:
    try:
        result = await Runner.run(agent, prompt, max_turns=max_turns)
    except Exception as exc:  # includes MaxTurnsExceeded
        if type(exc).__name__ == "MaxTurnsExceeded":
            return SdkRun(final_answer=f"[max turns exceeded: {exc}]", hit_max_iterations=True)
        raise

    calls = [item for item in result.new_items if isinstance(item, ToolCallItem)]
    outputs = [item for item in result.new_items if isinstance(item, ToolCallOutputItem)]

    names = [str(getattr(c.raw_item, "name", "?")) for c in calls]
    rejected = [str(o.output).startswith(REJECTED_PREFIX) for o in outputs]

    return SdkRun(
        final_answer=str(result.final_output),
        iterations=len(result.raw_responses),
        tool_names=names,
        executed_names=[
            name
            for index, name in enumerate(names)
            if not (index < len(rejected) and rejected[index])
        ],
        tool_arguments=[
            (str(getattr(c.raw_item, "name", "?")), str(getattr(c.raw_item, "arguments", "")))
            for c in calls
        ],
    )


async def main() -> None:
    import expense_store

    expense_store.reset(seeded=True)

    print(f"USER: {TASK}")
    print("=" * 72)

    run = await run_expense_agent(TASK)

    print(f"Tool calls the SDK attempted ({len(run.tool_names)}):")
    for name, args in run.tool_arguments:
        print(f"  -> {name}({args})")

    print("=" * 72)
    print(f"\nRejected at the boundary: {run.rejected_count}")
    print(f"Model turns: {run.iterations}")
    print(f"\nFINAL ANSWER:\n{run.final_answer}\n")


if __name__ == "__main__":
    asyncio.run(main())
