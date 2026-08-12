"""
Spendly Lite v2 — the golden dataset (Layer 3, "Proof").

    uv run python 02_typed_tools/solutions/check_expenses.py            # from scratch
    uv run python 02_typed_tools/solutions/check_expenses.py --impl sdk # Agents SDK

Chapter 1's five cases, plus two that only became askable in Chapter 2, and one
assertion running through all of them that Chapter 1 could not express.

WHAT CHANGED, AND WHY IT MATTERS
--------------------------------
Chapter 1 asserted on `tool_names` — "was log_expense called?". In Chapter 2
that question is ambiguous, because a call can now be REJECTED at the boundary
and never reach the function body. `log_expense` appearing in `tool_names` no
longer implies anything was written.

So the checks below use `executed_names` for "did it actually happen" and keep
`tool_names` only for "did it try". Getting this distinction wrong is the most
likely way to write an eval that passes a broken agent.

WHAT THIS FILE IS **NOT** FOR
-----------------------------
Every case here costs real API calls and takes minutes. Before adding one, ask
whether `test_expense_tools.py` could answer the same question for free. "Is a
negative amount rejected?" belongs there — it is a property of the boundary, not
of the agent. What belongs HERE is behaviour that requires a model: does it ask
instead of guessing, does it recover from a rejection, does it refuse cleanly.

Note: each case is a real round-trip and the Gemini free tier allows ~15
requests/minute, so the harness paces itself. Expect ~5 minutes.
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
    """Both implementations expose these. That is all the harness needs."""

    final_answer: str
    iterations: int
    hit_max_iterations: bool

    @property
    def tool_names(self) -> list[str]: ...

    @property
    def executed_names(self) -> list[str]: ...

    @property
    def rejected_count(self) -> int: ...


def normalise(text: str) -> str:
    """Strip thousands separators so '16,000' and '16000' both match."""
    return text.replace(",", "").lower()


def logged_rows() -> list[expense_store.Expense]:
    """Expenses written during this case (seeds are tagged and excluded)."""
    return [r for r in all_expenses() if r["notes"] != "seed"]


def wrote_nothing(run: RunLike) -> tuple[str, bool]:
    """
    The assertion that appears in six of the eight cases.

    Note it checks the LEDGER, not the tool list. An eval that asserts
    "log_expense was not called" is asserting on the agent's route; this asserts
    on the outcome. The agent is allowed to try and be stopped — that is the
    boundary doing its job, and it is not a failure.
    """
    return ("nothing was written to the ledger", len(logged_rows()) == 0)


# -----------------------------------------------------------------------------
# The cases.
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
        ("log_expense actually executed", "log_expense" in run.executed_names),
        ("the budget was looked up, not recalled", "get_budget" in run.executed_names),
        ("the month total came from a tool", "month_total" in run.executed_names),
        (f"the answer states {remaining:.0f} remaining", str(int(remaining)) in answer),
        ("at least 3 tools ran (real chaining)", len(run.executed_names) >= 3),
        # CAUSAL order: reading a total before writing to it returns a stale
        # number, and no correct arithmetic afterwards can fix that.
        (
            "month_total was read AFTER the write",
            "log_expense" in run.executed_names
            and "month_total" in run.executed_names
            and run.executed_names.index("log_expense") < run.executed_names.index("month_total"),
        ),
        # New in Chapter 2. A clean prompt with a valid amount and a real
        # category should not need the boundary at all. Rejections on the happy
        # path mean the schema is not telling the model what it needs.
        ("no rejections on the happy path", run.rejected_count == 0),
        ("budget not exhausted", not run.hit_max_iterations),
    ]


def case_2(run: RunLike) -> list[tuple[str, bool]]:
    """Read-only query. A question must never mutate the ledger."""
    answer = normalise(run.final_answer)
    return [
        wrote_nothing(run),
        ("log_expense did not execute", "log_expense" not in run.executed_names),
        ("month_total executed", "month_total" in run.executed_names),
        (f"the answer states {SEEDED_FOOD_TOTAL:.0f}", str(int(SEEDED_FOOD_TOTAL)) in answer),
    ]


def case_3(run: RunLike) -> list[tuple[str, bool]]:
    """
    Invalid category. In Chapter 1 the tool body rejected it; now the ENUM does,
    before the body is reached.

    The agent is free to attempt the call — it cannot know 'astrology' is
    invalid until it reads the schema or gets rejected. What it must not do is
    end up with a wrong row in the ledger, or tell the user it logged one.
    """
    answer = run.final_answer.lower()
    return [
        wrote_nothing(run),
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
        wrote_nothing(run),
        ("log_expense did not execute", "log_expense" not in run.executed_names),
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
    The Chapter 1 trap, re-run.

    In Chapter 1 this case could fail in a specific, nasty way: a helpful model
    normalises -450 to 450, the guard never sees a negative number, and the
    ledger ends up confidently wrong. `Amount` with `gt=0` closes the first half
    of that hole. The second half — the model silently flipping the sign — is
    still a judgement call, which is why the check tests the ledger and not just
    the tool.
    """
    answer = run.final_answer.lower()
    return [
        wrote_nothing(run),
        (
            "no expense was logged at 450 either",
            not any(r["amount"] == 450.0 for r in logged_rows()),
        ),
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


def case_6(run: RunLike) -> list[tuple[str, bool]]:
    """
    RECOVERY — the case Chapter 1 could not ask.

    The date is given in a format the schema forbids. The agent should be able
    to fix it without help, because the rejection tells it exactly what shape is
    required. This is the payoff for writing error messages as instructions:
    a boundary that only says "no" costs a turn; one that says "no, and here is
    the shape" costs a turn and buys a correct call.

    The check deliberately ACCEPTS a rejection happening. Zero rejections is
    also a pass — a model that reads the pattern out of the schema and converts
    the date before calling is doing better, not worse.
    """
    rows = logged_rows()
    return [
        ("exactly one expense was written", len(rows) == 1),
        ("it was logged at 1200", bool(rows) and rows[0]["amount"] == 1200.0),
        ("the date was normalised to 2026-08-05", bool(rows) and rows[0]["date"] == "2026-08-05"),
        ("categorised as Transportation", bool(rows) and rows[0]["category"] == "Transportation"),
        ("log_expense executed in the end", "log_expense" in run.executed_names),
        ("it recovered inside the budget", not run.hit_max_iterations),
    ]


def case_7(run: RunLike) -> list[tuple[str, bool]]:
    """
    The rule types cannot hold.

    'Not in the future' depends on the clock, so no schema can express it and
    the guard stays inside `log_expense`. It raises ToolError, which means it is
    recoverable in exactly the same way a schema rejection is — the model gets
    the message and another turn.

    A student who moved that guard into the signature will fail this case, and
    should: they will have made today's date part of a type.
    """
    answer = run.final_answer.lower()
    return [
        wrote_nothing(run),
        (
            "the reply mentions the date problem",
            any(p in answer for p in ("future", "2099", "date", "cannot", "can't")),
        ),
        (
            "it did not invent today's date instead",
            not any(r["amount"] == 3000.0 for r in logged_rows()),
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
    Case(
        6,
        "Log 1200 at Careem for transportation on 05/08/2026 (the 5th of August).",
        "Recovers from the date format, logs it as 2026-08-05",
        case_6,
    ),
    Case(
        7,
        "Log 3000 at Metro for groceries on 2099-01-01.",
        "Refuses the future date, writes nothing",
        case_7,
    ),
]


# -----------------------------------------------------------------------------
# Runner adapters — one per implementation. The dataset does not change between
# them. That is the point: an eval describes the BEHAVIOUR you require, not the
# code that produces it.
# -----------------------------------------------------------------------------


def run_from_scratch(prompt: str) -> RunLike:
    from expense_agent import SYSTEM_PROMPT
    from expense_tools import ALL_TOOLS
    from loop import run_agent

    return run_agent(
        user_message=prompt,
        tools=ALL_TOOLS,
        system_prompt=SYSTEM_PROMPT,
        verbose=False,
    )


def run_with_sdk(prompt: str) -> RunLike:
    from expense_agent_sdk import run_expense_agent

    return asyncio.run(run_expense_agent(prompt))


def main(impl: str) -> int:
    runner = run_with_sdk if impl == "sdk" else run_from_scratch
    label = "OpenAI Agents SDK" if impl == "sdk" else "from scratch"

    print(f"\nSpendly Lite v2 — golden dataset, implementation: {label}")

    total_checks = 0
    total_passed = 0
    rows: list[str] = []

    for index, case in enumerate(CASES):
        if index > 0:
            time.sleep(PAUSE_BETWEEN_CASES)  # free-tier rate limit

        expense_store.reset(seeded=True)

        print("\n" + "=" * 72)
        print(f"CASE {case.number}: {case.prompt}")
        print(f"EXPECTED: {case.expectation}")
        print("=" * 72)

        run = runner(case.prompt)

        print(f"ANSWER  : {run.final_answer.strip()[:300]}")
        print(f"ATTEMPTED: {run.tool_names or 'none'}")
        print(f"EXECUTED : {run.executed_names or 'none'}  |  rejected: {run.rejected_count}")

        checks = case.verify(run)
        for check_label, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {check_label}")

        passed = sum(1 for _, ok in checks if ok)
        total_checks += len(checks)
        total_passed += passed
        rows.append(
            f"| {case.number} | {passed}/{len(checks)} | "
            f"{', '.join(run.executed_names) or 'none'} | {run.rejected_count} | "
            f"{run.iterations} | {'PASS' if passed == len(checks) else 'FAIL'} |"
        )

    expense_store.reset(seeded=True)

    print("\n" + "=" * 72)
    print(f"RESULTS — {label} — month {current_month()}")
    print("| # | Checks | Tools executed | Rejected | Turns | Pass? |")
    print("|---|--------|----------------|----------|-------|-------|")
    for row in rows:
        print(row)
    print(f"\n{total_passed}/{total_checks} checks passed across {len(CASES)} cases.")

    return 0 if total_passed == total_checks else 1


if __name__ == "__main__":
    implementation = "sdk" if "--impl" in sys.argv and "sdk" in sys.argv else "scratch"
    sys.exit(main(implementation))
