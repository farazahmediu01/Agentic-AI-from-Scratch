"""
Spendly Lite — the check harness behind RUNS.md (Layer 3, "Proof").

Five hand-written cases with expected behaviour, asserted automatically, and
runnable against EITHER implementation:

    uv run python 01_agent_loop/solutions/check_expenses.py            # from scratch
    uv run python 01_agent_loop/solutions/check_expenses.py --impl sdk # Agents SDK

The dataset does not change between the two. That is the whole point: an eval
describes the BEHAVIOUR you require, not the code that produces it. When you
migrate an agent to a framework, the eval is what tells you the migration was
honest.

This is a golden dataset with 5 rows. The evals chapter grows it to 50 and adds
an LLM judge for the cases where "correct" is a paragraph, not a number.

Note: each case is a real API round-trip and the Gemini free tier allows ~15
requests/minute, so the harness paces itself. Expect ~3-4 minutes.
"""

from __future__ import annotations

import asyncio
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import expense_store
from expense_store import MONTHLY_BUDGETS, SEEDED_FOOD_TOTAL, all_expenses, current_month

PAUSE_BETWEEN_CASES = 30.0


class RunLike(Protocol):
    """
    Both implementations expose these. That is all the harness needs.

    `tool_names` is declared read-only (a property) because our AgentRun computes
    it and the SDK adapter stores it. A protocol should ask for the least it can
    live with — demand a mutable attribute and one of the two would not fit.
    """

    final_answer: str
    iterations: int
    hit_max_iterations: bool

    @property
    def tool_names(self) -> list[str]: ...


def normalise(text: str) -> str:
    """Strip thousands separators so '16,000' and '16000' both match."""
    return text.replace(",", "").lower()


def logged_rows() -> list[expense_store.Expense]:
    """Expenses written during this case (seeds are tagged and excluded)."""
    return [r for r in all_expenses() if r["notes"] != "seed"]


# -----------------------------------------------------------------------------
# The five cases. `verify` returns (label, passed) pairs.
# -----------------------------------------------------------------------------


def case_1(run: RunLike) -> list[tuple[str, bool]]:
    """Happy path: log an expense, then chain budget math on top of it."""
    answer = normalise(run.final_answer)
    rows = logged_rows()
    remaining = MONTHLY_BUDGETS["Food & Dining"] - (SEEDED_FOOD_TOTAL + 1500)
    return [
        ("exactly one expense was written", len(rows) == 1),
        ("it was logged at 1500", bool(rows) and rows[0]["amount"] == 1500.0),
        ("categorised as Food & Dining", bool(rows) and rows[0]["category"] == "Food & Dining"),
        ("vendor recorded as KFC", bool(rows) and "kfc" in rows[0]["vendor"].lower()),
        ("log_expense was called", "log_expense" in run.tool_names),
        ("the budget was looked up, not recalled", "get_budget" in run.tool_names),
        ("the month total came from a tool", "month_total" in run.tool_names),
        (f"the answer states {remaining:.0f} remaining", str(int(remaining)) in answer),
        ("at least 3 tool calls (real chaining)", len(run.tool_names) >= 3),
        # CAUSAL order, not incidental order. Most sequences are the model's
        # business — but reading a total before writing to it returns a stale
        # number, and no amount of correct arithmetic afterwards can fix that.
        # Assert order only when the order changes the answer.
        (
            "month_total was read AFTER the write, not before",
            (
                "log_expense" in run.tool_names
                and "month_total" in run.tool_names
                and run.tool_names.index("log_expense") < run.tool_names.index("month_total")
            ),
        ),
        ("budget not exhausted", not run.hit_max_iterations),
    ]


def case_2(run: RunLike) -> list[tuple[str, bool]]:
    """Read-only query. A question must never mutate the ledger."""
    answer = normalise(run.final_answer)
    return [
        ("NOTHING was written", len(logged_rows()) == 0),
        ("log_expense was not called", "log_expense" not in run.tool_names),
        ("month_total was called", "month_total" in run.tool_names),
        (f"the answer states {SEEDED_FOOD_TOTAL:.0f}", str(int(SEEDED_FOOD_TOTAL)) in answer),
    ]


def case_3(run: RunLike) -> list[tuple[str, bool]]:
    """Invalid category: offer the real options, write nothing."""
    answer = run.final_answer.lower()
    return [
        ("NOTHING was written", len(logged_rows()) == 0),
        (
            "the reply names real categories",
            sum(c in answer for c in ("food", "transportation", "shopping", "miscellaneous")) >= 2,
        ),
        (
            "it does not pretend the expense was logged",
            not any(
                p in answer
                for p in ("i've logged", "i have logged", "logged successfully", "recorded it")
            ),
        ),
    ]


def case_4(run: RunLike) -> list[tuple[str, bool]]:
    """Missing information: ask, never invent."""
    answer = run.final_answer.lower()
    return [
        ("NOTHING was written", len(logged_rows()) == 0),
        ("log_expense was not called", "log_expense" not in run.tool_names),
        (
            "it asks for the amount or the vendor",
            ("amount" in answer)
            or ("vendor" in answer)
            or ("how much" in answer)
            or ("where" in answer),
        ),
    ]


def case_5(run: RunLike) -> list[tuple[str, bool]]:
    """
    The trap. A negative amount must not be silently 'fixed'.

    The tool raises on amount <= 0 — but that guard only fires if the negative
    value actually reaches it. A helpful model will normalise -450 to 450 and
    the ledger ends up confidently wrong. This case exists to catch that.
    """
    answer = run.final_answer.lower()
    return [
        ("NOTHING was written", len(logged_rows()) == 0),
        (
            "no expense was logged at 450 either",
            not any(r["amount"] == 450.0 for r in logged_rows()),
        ),
        # Broadened after a real failure: the SDK build replied "I cannot log that
        # expense. Please provide a positive amount" — correct behaviour that an
        # earlier, narrower keyword list scored as a FAIL. Match the MEANING the
        # user needs (refusal + what to do next), not one phrasing of it.
        (
            "the reply refuses and asks for a valid amount",
            any(
                p in answer
                for p in (
                    "negative",
                    "-450",
                    "positive",
                    "cannot",
                    "can't",
                    "greater than zero",
                    "invalid",
                    "confirm",
                )
            ),
        ),
    ]


@dataclass
class Case:
    number: int
    prompt: str
    expectation: str
    verify: Callable[[RunLike], list[tuple[str, bool]]]


CASES: list[Case] = [
    Case(
        1,
        "I spent 1500 at KFC on lunch today. Log it, then tell me how much of my "
        "food budget is left this month.",
        f"Logged; PKR {MONTHLY_BUDGETS['Food & Dining'] - SEEDED_FOOD_TOTAL - 1500:,.0f} left",
        case_1,
    ),
    Case(
        2,
        "How much have I spent on food this month?",
        f"PKR {SEEDED_FOOD_TOTAL:,.0f}, nothing written",
        case_2,
    ),
    Case(
        3,
        "Log 2000 spent at Al-Falah Astrology under the astrology category.",
        "Offers the real categories, writes nothing",
        case_3,
    ),
    Case(4, "Log an expense for me.", "Asks for amount and vendor, writes nothing", case_4),
    Case(
        5,
        "Log -450 at Imtiaz Supermarket for groceries.",
        "Refuses the negative amount, writes nothing",
        case_5,
    ),
]


# -----------------------------------------------------------------------------
# Runner adapters — one per implementation.
# -----------------------------------------------------------------------------


def run_from_scratch(prompt: str) -> RunLike:
    from expense_agent import SYSTEM_PROMPT
    from expense_tools import TOOL_REGISTRY, TOOL_SCHEMAS
    from loop import run_agent

    run = run_agent(
        user_message=prompt,
        tool_registry=TOOL_REGISTRY,
        tool_schemas=TOOL_SCHEMAS,
        system_prompt=SYSTEM_PROMPT,
        verbose=False,
    )
    return run  # AgentRun already satisfies RunLike


def run_with_sdk(prompt: str) -> RunLike:
    from expense_agent_sdk import run_expense_agent

    return asyncio.run(run_expense_agent(prompt))


def main(impl: str) -> int:
    runner = run_with_sdk if impl == "sdk" else run_from_scratch
    label = "OpenAI Agents SDK" if impl == "sdk" else "from scratch"

    print(f"\nSpendly Lite v1 — golden dataset, implementation: {label}")

    total_checks = 0
    total_passed = 0
    rows: list[str] = []

    for index, case in enumerate(CASES):
        if index > 0:
            time.sleep(PAUSE_BETWEEN_CASES)  # free-tier rate limit

        # Every case starts from the same known ledger. No leftover state.
        expense_store.reset(seeded=True)

        print("\n" + "=" * 72)
        print(f"CASE {case.number}: {case.prompt}")
        print(f"EXPECTED: {case.expectation}")
        print("=" * 72)

        run = runner(case.prompt)

        print(f"ANSWER : {run.final_answer.strip()[:300]}")
        print(f"TOOLS  : {run.tool_names or 'none'}  |  turns: {run.iterations}")

        checks = case.verify(run)
        for check_label, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {check_label}")

        passed = sum(1 for _, ok in checks if ok)
        total_checks += len(checks)
        total_passed += passed
        rows.append(
            f"| {case.number} | {passed}/{len(checks)} | "
            f"{', '.join(run.tool_names) or 'none'} | {run.iterations} | "
            f"{'PASS' if passed == len(checks) else 'FAIL'} |"
        )

    expense_store.reset(seeded=True)

    print("\n" + "=" * 72)
    print(f"RESULTS — {label} — month {current_month()}")
    print("| # | Checks | Tools called | Turns | Pass? |")
    print("|---|--------|--------------|-------|-------|")
    for row in rows:
        print(row)
    print(f"\n{total_passed}/{total_checks} checks passed across {len(CASES)} cases.")

    return 0 if total_passed == total_checks else 1


if __name__ == "__main__":
    implementation = "sdk" if "--impl" in sys.argv and "sdk" in sys.argv else "scratch"
    sys.exit(main(implementation))
