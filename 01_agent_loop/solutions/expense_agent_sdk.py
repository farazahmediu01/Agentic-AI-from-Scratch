"""
Spendly Lite v1 — SDK build (Layer 4 + 6).

Same agent as `expense_agent.py`. Same system prompt. Same tools. Same
acceptance checklist. Graded by the same harness.

Run:  uv run python 01_agent_loop/solutions/expense_agent_sdk.py

What disappeared compared with the from-scratch build:
  - loop.py                (~200 lines)  -> Runner.run
  - TOOL_SCHEMAS           (~140 lines)  -> @function_tool reads type hints + docstrings
  - TOOL_REGISTRY                        -> tools=[...]

What did NOT disappear: the system prompt, the tool logic, and the validation.
The SDK removes plumbing. It does not remove judgement — the rules that stop
this agent writing a wrong ledger are still yours to write.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Literal

from agents import Agent, Runner, function_tool
from agents.items import ToolCallItem

import expense_tools as t
from expense_agent import SYSTEM_PROMPT, TASK
from expense_store import CATEGORIES
from shared.models import make_model

MODEL = make_model()

# The SDK can enforce a closed set of categories in the schema itself, which the
# hand-rolled version could only describe in prose. Note what this buys you: an
# invalid category is now rejected *before* your function runs.
Category = Literal[
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Bills & Utilities",
    "Entertainment",
    "Health & Medical",
    "Education",
    "Groceries",
    "Office Supplies",
    "Miscellaneous",
]

assert set(CATEGORIES) == set(Category.__args__), "Literal drifted from CATEGORIES"


# -----------------------------------------------------------------------------
# The same seven tools. The business logic is imported unchanged from
# expense_tools.py — only the agent-facing wrapper changes. That is the honest
# way to compare two implementations: hold the logic constant.
# -----------------------------------------------------------------------------


@function_tool
def get_today() -> str:
    """Get today's date as YYYY-MM-DD."""
    return t.get_today()


@function_tool
def log_expense(vendor: str, amount: float, category: Category, expense_date: str = "") -> str:
    """Record one expense in the user's ledger. This writes to storage.

    Call it only when the vendor, amount and category are all known. Never call
    it with guessed or silently corrected values.
    """
    return t.log_expense(vendor, amount, category, expense_date)


@function_tool
def month_total(category: Category, month: str = "") -> float:
    """Total already spent in one category during one month (YYYY-MM, defaults to this month)."""
    return t.month_total(category, month)


@function_tool
def get_budget(category: Category) -> float:
    """Get the monthly budget in PKR for one category."""
    return t.get_budget(category)


@function_tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a. Use it to compute budget remaining: subtract(budget, spent)."""
    return t.subtract(a, b)


@function_tool
def list_recent(limit: int = 5) -> str:
    """Show the most recent expenses the user recorded."""
    return t.list_recent(limit)


@function_tool
def list_categories() -> str:
    """List every valid expense category."""
    return t.list_categories()


agent = Agent(
    name="Spendly Lite",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    tools=[get_today, log_expense, month_total, get_budget, subtract, list_recent, list_categories],
)


# -----------------------------------------------------------------------------
# Adapter: make an SDK result look like our AgentRun.
#
# This is the bit worth studying. Our eval harness asserts on `final_answer`,
# `tool_names` and `iterations`. Those facts exist in both implementations —
# they are just spelled differently. Thirty lines of adapter let ONE golden
# dataset grade BOTH builds. A good eval does not care how you built the agent.
# -----------------------------------------------------------------------------


@dataclass
class SdkRun:
    final_answer: str
    iterations: int = 0
    tool_names: list[str] = field(default_factory=list)
    hit_max_iterations: bool = False
    tool_arguments: list[tuple[str, str]] = field(default_factory=list)

    @property
    def error_count(self) -> int:
        return 0  # the SDK returns tool errors to the model; we don't see them here


async def run_expense_agent(prompt: str, max_turns: int = 15) -> SdkRun:
    try:
        result = await Runner.run(agent, prompt, max_turns=max_turns)
    except Exception as exc:  # includes MaxTurnsExceeded
        if type(exc).__name__ == "MaxTurnsExceeded":
            return SdkRun(final_answer=f"[max turns exceeded: {exc}]", hit_max_iterations=True)
        raise

    calls = [item for item in result.new_items if isinstance(item, ToolCallItem)]
    return SdkRun(
        final_answer=str(result.final_output),
        # One model response per turn; tool calls issued in the same turn share it.
        iterations=len(result.raw_responses),
        tool_names=[getattr(c.raw_item, "name", "?") for c in calls],
        tool_arguments=[
            (getattr(c.raw_item, "name", "?"), str(getattr(c.raw_item, "arguments", "")))
            for c in calls
        ],
    )


async def main() -> None:
    print(f"USER: {TASK}")
    print("=" * 72)

    run = await run_expense_agent(TASK)

    print(f"Tool calls the SDK ran ({len(run.tool_names)}):")
    for name, args in run.tool_arguments:
        print(f"  -> {name}({args})")

    print("=" * 72)
    print(f"\nFINAL ANSWER:\n{run.final_answer}\n")
    print(f"Model turns: {run.iterations}")


if __name__ == "__main__":
    asyncio.run(main())
