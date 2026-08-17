"""
Spendly Lite v3 — the golden dataset (Layer 3, "Proof").

    uv run python 03_structured_outputs/solutions/check_expenses.py

WHAT CHANGED, AND WHY IT IS THE POINT OF THE CHAPTER
-----------------------------------------------------
Chapter 2's version of this file asked questions like:

    ("the answer states 16000 remaining", "16000" in answer)
    ("it asks for the amount",            "how much" in answer or "amount" in answer)
    ("the reply refuses",                 any(p in answer for p in ("negative", "cannot", ...)))

Every one of those is a **classifier built out of `str.find`**, and every one is
wrong in both directions:

  * `"16000" in answer` passes on "you have spent 16000 of your 16000 budget",
    which is the opposite of what it means to check.
  * `"amount" in answer` passes on "I logged that amount for you."
  * The refusal check is a list of eight hopeful synonyms that will miss the
    ninth phrasing the model uses next Tuesday.

Chapter 3 deletes all of them. The assertions below read fields:

    run.branch == "logged"
    run.reply.logged.remaining == 17500
    run.reply.need_more_info.missing == ["category"]
    run.reply.refused.reason == "negative_amount"

Those are not heuristics about wording. They are the shape the model chose, and
they cannot be satisfied by an unlucky substring.

> **This is why structured outputs sit at Chapter 3 rather than later.** They are
> not a feature; they are what makes evaluation possible. Chapter 6 automates
> evals, and it needs assertions that mean something. Ch2 made the tool boundary
> testable and bought 46 unit tests. Ch3 makes the OUTPUT testable.

THE REGRESSION RULE
-------------------
Cases 1-7 are Chapter 2's, unchanged in intent. They must still pass. A chapter
that breaks the previous chapter's dataset is not finished, however good its new
capability is. Cases 8 and 9 could not have been written before this chapter.

Each case is a real round-trip and the Gemini free tier allows ~15 requests per
minute, so the harness paces itself. Expect ~6 minutes.
"""

from __future__ import annotations

import asyncio
import io
import sys
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Protocol

import _bootstrap  # noqa: F401  -- must precede every spine import
import expense_store
from expense_store import MONTHLY_BUDGETS, SEEDED_FOOD_TOTAL, all_expenses
from replies import SpendlyReply

# The free tier allows ~15 requests/minute. A v3 case costs 4-10 of them, because
# `output_type` adds a final structured-output turn on top of the tool calls. At a
# 30s pause the harness poisons its own run: a 429 mid-case exhausts the SDK's
# internal retries, the run dies with MaxTurnsExceeded, and every check in that
# case fails for a reason that has nothing to do with the agent.
#
# Worth naming, because it is a whole class of bad eval: **an eval that fails for
# infrastructure reasons teaches you nothing and costs you trust in the suite.**
# If your dataset is flaky, fix the harness before you touch the agent.
PAUSE_BETWEEN_CASES = 60.0


class RunLike(Protocol):
    """What the harness needs from a run. Now includes the typed reply."""

    reply: SpendlyReply | None
    final_answer: str
    iterations: int
    hit_max_iterations: bool
    output_error: str

    @property
    def tool_names(self) -> list[str]: ...

    @property
    def executed_names(self) -> list[str]: ...

    @property
    def rejected_count(self) -> int: ...

    @property
    def branch(self) -> str: ...


Checks = list[tuple[str, bool]]


def logged_rows() -> list[expense_store.Expense]:
    """Expenses written during this case (seeds are tagged and excluded)."""
    return [r for r in all_expenses() if r["notes"] != "seed"]


def wrote_nothing(run: RunLike) -> tuple[str, bool]:
    """Asserts on the OUTCOME (the ledger), not on the agent's route."""
    return ("nothing was written to the ledger", len(logged_rows()) == 0)


def produced_a_reply(run: RunLike) -> tuple[str, bool]:
    """
    New in Chapter 3, and it belongs in every case.

    In v2 the agent could not fail to produce an answer -- any string at all was
    acceptable. Now the reply must satisfy a schema AND the exactly-one-branch
    validator, so "produced no valid reply" is a distinct failure worth naming.
    """
    return ("a valid reply object was produced", run.reply is not None and not run.output_error)


# -----------------------------------------------------------------------------
# Cases 1-7: Chapter 2's dataset, with substring checks replaced by field checks.
# -----------------------------------------------------------------------------


def case_1(run: RunLike) -> Checks:
    """Happy path: log an expense, then chain budget math on top of it."""
    rows = logged_rows()
    remaining = MONTHLY_BUDGETS["Food & Dining"] - (SEEDED_FOOD_TOTAL + 1500)
    logged = run.reply.logged if run.reply else None
    return [
        produced_a_reply(run),
        ("the branch is 'logged'", run.branch == "logged"),
        ("exactly one expense was written", len(rows) == 1),
        ("it was logged at 1500", bool(rows) and rows[0]["amount"] == 1500.0),
        ("categorised as Food & Dining", bool(rows) and rows[0]["category"] == "Food & Dining"),
        ("log_expense actually executed", "log_expense" in run.executed_names),
        ("the budget was looked up, not recalled", "get_budget" in run.executed_names),
        ("the month total came from a tool", "month_total" in run.executed_names),
        # THE CHAPTER 3 UPGRADE. v2 asked `"17500" in answer`. This asks whether
        # the number the agent REPORTED equals the number that is true -- and it
        # can only ask that because `remaining` is a float on a typed object.
        (
            f"reply.logged.amount == 1500 (got {logged.amount if logged else None})",
            logged is not None and logged.amount == 1500.0,
        ),
        (
            f"reply.logged.remaining == {remaining:.0f} "
            f"(got {logged.remaining if logged else None})",
            logged is not None and logged.remaining == remaining,
        ),
        ("reply.logged.vendor is KFC", logged is not None and "kfc" in logged.vendor.lower()),
        ("at least 3 tools ran (real chaining)", len(run.executed_names) >= 3),
        (
            "month_total was read AFTER the write",
            "log_expense" in run.executed_names
            and "month_total" in run.executed_names
            and run.executed_names.index("log_expense") < run.executed_names.index("month_total"),
        ),
        ("no rejections on the happy path", run.rejected_count == 0),
        ("budget not exhausted", not run.hit_max_iterations),
    ]


def case_2(run: RunLike) -> Checks:
    """Read-only query. A question must never mutate the ledger."""
    reported = run.reply.reported if run.reply else None
    return [
        produced_a_reply(run),
        # v2 could only check that the string contained "9000". This checks that
        # the agent classified its own action as a report rather than a write --
        # a distinction no substring can make.
        ("the branch is 'reported'", run.branch == "reported"),
        wrote_nothing(run),
        ("log_expense did not execute", "log_expense" not in run.executed_names),
        ("month_total executed", "month_total" in run.executed_names),
        (
            f"reply.reported.spent == {SEEDED_FOOD_TOTAL:.0f} "
            f"(got {reported.spent if reported else None})",
            reported is not None and reported.spent == SEEDED_FOOD_TOTAL,
        ),
    ]


def case_3(run: RunLike) -> Checks:
    """Invalid category. The enum rejects it before any body runs."""
    return [
        produced_a_reply(run),
        wrote_nothing(run),
        # v2 counted category words in the prose and checked for absence of the
        # phrase "I've logged". Both were guesswork. Either branch is defensible
        # here -- ask, or refuse -- but "logged" is not, and now that is exact.
        ("it did not claim to log anything", run.branch in {"need_more_info", "refused"}),
    ]


def case_4(run: RunLike) -> Checks:
    """Missing information: ask, never invent."""
    need = run.reply.need_more_info if run.reply else None
    return [
        produced_a_reply(run),
        ("the branch is 'need_more_info'", run.branch == "need_more_info"),
        wrote_nothing(run),
        ("log_expense did not execute", "log_expense" not in run.executed_names),
        ("it names at least two missing fields", need is not None and len(need.missing) >= 2),
    ]


def case_5(run: RunLike) -> Checks:
    """The Chapter 1 trap: -450 must not become a confident 450."""
    refused = run.reply.refused if run.reply else None
    return [
        produced_a_reply(run),
        wrote_nothing(run),
        (
            "no expense was logged at 450 either",
            not any(r["amount"] == 450.0 for r in logged_rows()),
        ),
        ("the branch is 'refused'", run.branch == "refused"),
        # v2 searched the prose for any of eight synonyms for "no". This reads
        # the model's own classification of WHY -- which is a different and much
        # harder thing to fake.
        (
            f"reply.refused.reason == 'negative_amount' "
            f"(got {refused.reason if refused else None})",
            refused is not None and refused.reason == "negative_amount",
        ),
        (
            "it echoed the offending value back",
            refused is not None and "450" in refused.offending_value,
        ),
    ]


def case_6(run: RunLike) -> Checks:
    """RECOVERY: a date the schema forbids, fixed without help."""
    rows = logged_rows()
    return [
        produced_a_reply(run),
        ("the branch is 'logged'", run.branch == "logged"),
        ("exactly one expense was written", len(rows) == 1),
        ("it was logged at 1200", bool(rows) and rows[0]["amount"] == 1200.0),
        ("the date was normalised to 2026-08-05", bool(rows) and rows[0]["date"] == "2026-08-05"),
        ("categorised as Transportation", bool(rows) and rows[0]["category"] == "Transportation"),
        ("it recovered inside the budget", not run.hit_max_iterations),
    ]


def case_7(run: RunLike) -> Checks:
    """The rule types cannot hold: 'not in the future' depends on the clock."""
    refused = run.reply.refused if run.reply else None
    return [
        produced_a_reply(run),
        wrote_nothing(run),
        (
            "it did not invent today's date instead",
            not any(r["amount"] == 3000.0 for r in logged_rows()),
        ),
        ("the branch is 'refused'", run.branch == "refused"),
        (
            f"reply.refused.reason == 'future_date' (got {refused.reason if refused else None})",
            refused is not None and refused.reason == "future_date",
        ),
    ]


# -----------------------------------------------------------------------------
# Cases 8-9: only askable because the output has a shape.
# -----------------------------------------------------------------------------


def case_8(run: RunLike) -> Checks:
    """
    PRECISION OF THE ASK. Vendor and amount are given; the category is not.

    v2 could check that the reply contained a question mark. It could not check
    that the agent asked for the RIGHT thing. An agent that says "how much did
    you spend?" when you already told it 500 is broken in a way no substring
    test can see -- and it is a real failure mode, because a model that loses
    track of what it already knows will loop.
    """
    need = run.reply.need_more_info if run.reply else None
    return [
        produced_a_reply(run),
        ("the branch is 'need_more_info'", run.branch == "need_more_info"),
        wrote_nothing(run),
        (
            f"missing == ['category'] exactly (got {need.missing if need else None})",
            need is not None and need.missing == ["category"],
        ),
        ("it did not re-ask for the amount", need is not None and "amount" not in need.missing),
        ("it did not re-ask for the vendor", need is not None and "vendor" not in need.missing),
    ]


def case_9(run: RunLike) -> Checks:
    """
    ZERO IS NOT NEGATIVE, AND THE MODEL MUST SAY SO CORRECTLY.

    `Field(gt=0)` rejects 0 exactly as it rejects -450, so the boundary behaves
    identically. What differs is the EXPLANATION, and in v2 the explanation was
    unassertable prose. Here the reason enum has to be right.

    This is also a deliberate trap for the output model's design: `reason` has no
    `zero_amount` member, so the model must map 0 onto `negative_amount`. If your
    students argue that is a bad enum, they are right -- and arguing it is the
    exercise. See EXERCISES.md Challenge 2.
    """
    refused = run.reply.refused if run.reply else None
    return [
        produced_a_reply(run),
        wrote_nothing(run),
        ("the branch is 'refused'", run.branch == "refused"),
        ("no expense was written at any amount", len(logged_rows()) == 0),
        (
            f"reason is an amount problem (got {refused.reason if refused else None})",
            refused is not None and refused.reason in {"negative_amount", "other"},
        ),
    ]


@dataclass
class Case:
    number: int
    prompt: str
    expectation: str
    verify: Callable[[RunLike], Checks]


CASES: list[Case] = [
    Case(
        1,
        "I spent 1500 at KFC on lunch today. Log it, then tell me how much of my "
        "food budget is left this month.",
        "branch=logged, remaining reported as a number",
        case_1,
    ),
    Case(
        2, "How much have I spent on food this month?", "branch=reported, nothing written", case_2
    ),
    Case(
        3,
        "Log 2000 spent at Al-Falah Astrology under the astrology category.",
        "not 'logged'; writes nothing",
        case_3,
    ),
    Case(4, "Log an expense for me.", "branch=need_more_info, >=2 fields missing", case_4),
    Case(
        5,
        "Log -450 at Imtiaz Supermarket for groceries.",
        "branch=refused, reason=negative_amount",
        case_5,
    ),
    Case(
        6,
        "Log 1200 at Careem for transportation on 05/08/2026 (the 5th of August).",
        "branch=logged, date normalised to 2026-08-05",
        case_6,
    ),
    Case(
        7,
        "Log 3000 at Metro for groceries on 2099-01-01.",
        "branch=refused, reason=future_date",
        case_7,
    ),
    Case(8, "Log 500 at Metro.", "branch=need_more_info, missing==['category']", case_8),
    Case(9, "Log 0 at Metro for groceries.", "branch=refused, an amount problem", case_9),
]


def run_v3(prompt: str) -> RunLike:
    from expense_agent_v3 import run_expense_agent

    return asyncio.run(run_expense_agent(prompt))


def main() -> int:
    # This harness takes ~6 minutes. Python block-buffers stdout whenever it is
    # not attached to a terminal, so piping it to a file or a log shows nothing
    # at all until the very end -- which looks exactly like a hang.
    #
    # The isinstance guard is not defensive noise: `sys.stdout` is typed as the
    # TextIO protocol, which has no `reconfigure`. Under a redirect it is a
    # TextIOWrapper and does. Narrowing it is how you tell pyright the truth
    # instead of casting the check away.
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)

    total_checks = 0
    passed_checks = 0
    failed_cases: list[int] = []

    print("Spendly Lite v3 — golden dataset (9 cases)")
    print("Cases 1-7 are Chapter 2's, and must still pass. 8-9 are new.\n")

    for index, case in enumerate(CASES):
        expense_store.reset(seeded=True)
        print(f"CASE {case.number}: {case.prompt}")
        print(f"  expect: {case.expectation}")

        run = run_v3(case.prompt)
        checks = case.verify(run)

        case_ok = True
        for label, ok in checks:
            total_checks += 1
            passed_checks += ok
            case_ok &= ok
            print(f"    {'PASS' if ok else 'FAIL'}  {label}")

        if not case_ok:
            failed_cases.append(case.number)
        print(f"  branch={run.branch}  turns={run.iterations}  rejected={run.rejected_count}")
        if run.output_error:
            print(f"  OUTPUT ERROR: {run.output_error}")
        print()

        if index < len(CASES) - 1:
            time.sleep(PAUSE_BETWEEN_CASES)

    print("=" * 72)
    print(f"{passed_checks}/{total_checks} checks passed")
    if failed_cases:
        print(f"FAILED CASES: {failed_cases}")
    else:
        print("All cases passed.")
    return 0 if not failed_cases else 1


if __name__ == "__main__":
    raise SystemExit(main())
