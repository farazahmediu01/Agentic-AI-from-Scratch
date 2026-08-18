"""
Spendly Lite v4 — the multi-turn golden dataset (Layer 3, "Proof").

    uv run python 04_sessions_state/solutions/check_multiturn.py
    uv run python 04_sessions_state/solutions/check_multiturn.py --only 1,4

WHY THIS IS A SEPARATE FILE FROM check_expenses.py
---------------------------------------------------
It would be tidier to fold five multi-turn cases into Chapter 3's nine and run
one command. That was considered and rejected at spec time, for a reason that is
about operations rather than taste:

    a 2-turn case costs roughly twice the requests of a 1-turn case.

Folding these in takes one run from ~15 minutes to ~25 and roughly doubles the
odds that the free tier poisons it mid-flight -- which is exactly the failure
that cost a complete Chapter 3 verification run. Two commands, each at moderate
risk, beats one command at high risk. **When an eval gets long enough to fail
for infrastructure reasons, split it before you tune it.**

The single-turn regression lives in `check_regression.py`, which pushes Chapter
3's nine cases through THIS chapter's agent.

WHAT ONLY A MULTI-TURN DATASET CAN ASK
---------------------------------------
Every case here is a question that is unaskable in one turn:

    M1  does the agent USE what it was told earlier?
    M2  the control -- without a session, does it fail to?
    M3  does one conversation stay out of another?
    M4  does it re-read a fact that changed while nobody was looking?
    M5  does the same question get a different answer for a different user?

M2 is the one to defend if somebody calls it wasteful. **An eval with no control
cannot distinguish "the session works" from "the model guessed well",** and this
chapter's own demo script proved that is not a hypothetical: with the session
removed but the context object shared, the agent still recovered the answer.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import sys
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from agents.memory.session import Session

import _bootstrap  # noqa: F401  -- must precede every spine import
import expense_store
from check_expenses import Checks, RunLike, produced_a_reply
from expense_agent_v4 import make_session, run_expense_agent
from expense_store import SEEDED_FOOD_TOTAL, Expense, all_expenses
from spendly_context import AYESHA, FARAZ, User


class MultiTurnRun(RunLike, Protocol):
    """
    Chapter 3's contract, widened -- not edited.

    Two of the checks below assert on `session_items`, which Chapter 3's
    `RunLike` has never heard of. There were three ways to make that type-check
    and only one of them is right:

        1. add the field to Chapter 3's Protocol       -- edits a shipped chapter
                                                          to serve a later one
        2. drop the Protocol and import v4's SdkRun    -- couples the dataset to
                                                          one concrete class
        3. inherit from it here                        <- this

    Protocols compose. `MultiTurnRun` is "everything Chapter 3 needed, plus one
    thing Chapter 4 needs", and `SdkRun` satisfies it without being told either
    exists. Chapter 3's file did not change; `check_regression.py` still passes
    the same object to the same checks.
    """

    input_tokens: int
    session_items: int
    session_text: str


# Two turns per case, five cases: ten runs, each 2-5 requests. Paced against the
# per-MINUTE limit (15/model/project). The per-DAY limit is 500 and this file
# spends 30-50 of it -- see check_expenses.py for why those two get confused.
PAUSE_BETWEEN_TURNS = 40.0
PAUSE_BETWEEN_CASES = 55.0

EXTERNAL_NOTE = "external"
EXTERNAL_AMOUNT = 5000.0


def agent_written_rows() -> list[Expense]:
    """
    Rows the AGENT wrote. Seeds and anything injected by the harness excluded.

    Chapter 3's `logged_rows()` excluded seeds only, which was enough while the
    harness never wrote to the ledger itself. Case M4 does, so the filter grows.
    """
    return [r for r in all_expenses() if r["notes"] not in {"seed", EXTERNAL_NOTE}]


def wrote_nothing(run: MultiTurnRun) -> tuple[str, bool]:
    return ("the agent wrote nothing to the ledger", len(agent_written_rows()) == 0)


def no_checks(run: MultiTurnRun) -> Checks:
    """A setup turn. It still runs, it just is not what the case is asking about."""
    return []


# -----------------------------------------------------------------------------
# The world can change between turns. This is what makes M4 possible.
# -----------------------------------------------------------------------------


def inject_expense_from_elsewhere() -> None:
    """
    Write to the ledger WITHOUT telling the agent.

    This is not a contrivance to make a test hard. It is Tuesday: the user logged
    a lunch from the mobile app, a bank sync imported a card transaction, their
    partner added a shared expense. Any product with more than one entry point
    has this, and an agent holding a conversation is by definition holding a
    stale copy of everything it was told.
    """
    expense_store.append(
        {
            "id": "EXP-EXTERNAL-001",
            "date": f"{expense_store.current_month()}-09",
            "vendor": "Imtiaz Supermarket",
            "amount": EXTERNAL_AMOUNT,
            "category": "Food & Dining",
            "notes": EXTERNAL_NOTE,
        }
    )


# -----------------------------------------------------------------------------
# Cases
# -----------------------------------------------------------------------------


def m1_turn2_logged_from_memory(run: MultiTurnRun) -> Checks:
    """
    THE CASE CHAPTER 3 WROTE AND COULD NOT ANSWER.

    Chapter 3's case 8 ended with a perfectly typed question -- `missing ==
    ["category"]` -- that the system was structurally incapable of hearing the
    answer to. The user's reply here is one word. For it to become a complete
    expense, the vendor and the amount have to survive from the previous turn.
    """
    rows = agent_written_rows()
    logged = run.reply.logged if run.reply else None
    return [
        produced_a_reply(run),
        ("the branch is 'logged'", run.branch == "logged"),
        ("exactly one expense was written", len(rows) == 1),
        ("amount 500 came from turn 1", bool(rows) and rows[0]["amount"] == 500.0),
        ("vendor 'Metro' came from turn 1", bool(rows) and "metro" in rows[0]["vendor"].lower()),
        ("category came from turn 2", bool(rows) and rows[0]["category"] == "Groceries"),
        (
            f"reply.logged.amount == 500 (got {logged.amount if logged else None})",
            logged is not None and logged.amount == 500.0,
        ),
        ("it did not ask for the amount again", run.branch != "need_more_info"),
        ("the session was actually used", run.session_items > 2),
        ("turn 1's 'Metro' is in this session's transcript", "Metro" in run.session_text),
    ]


def m2_control_cannot_complete(run: MultiTurnRun) -> Checks:
    """
    THE CONTROL. Identical turns, `session=None`.

    If this case ever passes the way M1 passes, M1 was proving nothing.
    """
    return [
        produced_a_reply(run),
        wrote_nothing(run),
        ("it did NOT log anything from a word it never heard", run.branch != "logged"),
        ("log_expense never executed", "log_expense" not in run.executed_names),
        ("no session was attached", run.session_items == 0),
    ]


def m3_other_session_is_deaf(run: MultiTurnRun) -> Checks:
    """
    Turn 1 went to one session_id. Turn 2 went to another. Nothing may cross.

    THIS CHECK WAS WRONG THE FIRST TIME, and how it was wrong is worth more than
    the case. It originally read:

        ("this session heard only its own turn", run.session_items <= 2)

    which failed at 6 -- because a run appends its OWN items to the session it is
    running in, so the count after turn 2 is never 2. The count was a PROXY for
    the real claim, and it was measuring the wrong conversation.

    There were two ways forward. Raise the threshold until it passes, or assert
    the actual claim. Raising it would have produced a green suite that no longer
    tested isolation at all -- `session_items <= 8` passes just as happily when
    the other conversation HAS leaked in.

    > **Never weaken a check to make a run pass.** If a check is wrong, it is
    > usually wrong about WHAT it asserts, not about the number. Fix the subject,
    > not the threshold.
    """
    return [
        produced_a_reply(run),
        wrote_nothing(run),
        ("the other conversation did not leak in", run.branch != "logged"),
        # The claim itself: the word 'Metro' was said in session m3_alpha and must
        # appear nowhere in m3_beta's transcript.
        ("'Metro' is absent from THIS session's transcript", "Metro" not in run.session_text),
        ("this session has a transcript of its own", run.session_items > 0),
    ]


def m4_reread_after_the_world_changed(run: MultiTurnRun) -> Checks:
    """
    STALE STATE -- the bug that persistence CAUSES. This is the chapter's section 8.

    Turn 1 asked how much had been spent on food. The agent called a tool, got
    7500, and said 7500. That number is now sitting in the transcript, in the
    agent's own words, and it is re-sent on every subsequent turn.

    Between the turns, 5000 of food spending arrived from somewhere else.

    So turn 2 has a cheap wrong answer and an expensive right one, and the cheap
    wrong answer is written in its own handwriting. Chapter 1's rule -- "use
    tools for every fact, never recall from memory" -- was easy to keep when
    there was no memory to recall from. A session is what makes it hard.
    """
    expected = SEEDED_FOOD_TOTAL + EXTERNAL_AMOUNT
    reported = run.reply.reported if run.reply else None
    got = reported.spent if reported else None
    return [
        produced_a_reply(run),
        ("the branch is 'reported'", run.branch == "reported"),
        ("month_total was called AGAIN on turn 2", "month_total" in run.executed_names),
        (
            f"reply.reported.spent == {expected:.0f} (got {got})",
            reported is not None and reported.spent == expected,
        ),
        (
            f"it did not repeat the stale {SEEDED_FOOD_TOTAL:.0f} from turn 1",
            reported is None or reported.spent != SEEDED_FOOD_TOTAL,
        ),
        wrote_nothing(run),
    ]


def _budget_check(user: User) -> Callable[[MultiTurnRun], Checks]:
    """One question, one user, one arithmetic truth. Built per user."""
    expected = user.budget_for("Food & Dining") - SEEDED_FOOD_TOTAL

    def verify(run: MultiTurnRun) -> Checks:
        reported = run.reply.reported if run.reply else None
        got = reported.remaining if reported else None
        return [
            produced_a_reply(run),
            ("the branch is 'reported'", run.branch == "reported"),
            ("the budget came from the context, via a tool", "get_budget" in run.executed_names),
            (
                f"{user.name}: remaining == {expected:.0f} (got {got})",
                reported is not None and reported.remaining == expected,
            ),
            wrote_nothing(run),
        ]

    return verify


# -----------------------------------------------------------------------------
# The harness
# -----------------------------------------------------------------------------


@dataclass
class Turn:
    prompt: str
    verify: Callable[[MultiTurnRun], Checks] = no_checks
    session_id: str | None = None
    # `user: User = FARAZ` is a TypeError at class-creation time, not a runtime
    # surprise -- `@dataclass` refuses any default it cannot hash, and a plain
    # (non-frozen, eq=True) dataclass sets `__hash__ = None`. The same rule that
    # protects you from `budgets: dict = {}` in spendly_context.py, arriving from
    # the other direction. The factory hands over the one shared FARAZ on purpose:
    # these are read-only in the harness, and a fresh copy per turn would quietly
    # make case M5's "same object, different user" claim untestable.
    user: User = field(default_factory=lambda: FARAZ)
    before: Callable[[], None] | None = None


@dataclass
class MultiCase:
    number: int
    name: str
    expectation: str
    turns: list[Turn] = field(default_factory=list)
    use_session: bool = True


CASES: list[MultiCase] = [
    MultiCase(
        1,
        "the answer to Chapter 3's question",
        "turn 2 is one word; the expense completes from turn 1",
        [
            Turn("Log 500 at Metro."),
            Turn("Groceries.", m1_turn2_logged_from_memory),
        ],
    ),
    MultiCase(
        2,
        "the control - no session",
        "turn 2 cannot complete anything",
        [
            Turn("Log 500 at Metro."),
            Turn("Groceries.", m2_control_cannot_complete),
        ],
        use_session=False,
    ),
    MultiCase(
        3,
        "session isolation",
        "a second session_id hears nothing from the first",
        [
            Turn("Log 500 at Metro.", session_id="m3_alpha"),
            Turn("Groceries.", m3_other_session_is_deaf, session_id="m3_beta"),
        ],
    ),
    MultiCase(
        4,
        "stale state",
        "the ledger changed between turns; turn 2 must re-read it",
        [
            Turn("How much have I spent on food this month?"),
            Turn(
                "And how much now?",
                m4_reread_after_the_world_changed,
                before=inject_expense_from_elsewhere,
            ),
        ],
    ),
    MultiCase(
        5,
        "the context decides the answer",
        "one prompt, two users, two different correct numbers",
        [
            Turn(
                "How much of my food budget is left this month?",
                _budget_check(FARAZ),
                user=FARAZ,
            ),
            Turn(
                "How much of my food budget is left this month?",
                _budget_check(AYESHA),
                user=AYESHA,
            ),
        ],
        use_session=False,
    ),
]


async def run_case(case: MultiCase) -> tuple[int, int, bool]:
    """
    Run every turn of one case. Only turns with checks contribute to the score.

    THE BUG THIS FUNCTION SHIPPED FIRST, because it is the one a multi-turn
    harness is built to make:

        session = make_session(...)          # inside the turn loop
        await session.clear_session()        # <- wipes turn 1 before turn 2 runs

    Case M1 then scored 2/9 with `branch=need_more_info` on turn 2, which is
    precisely what a broken session looks like -- and precisely what a broken
    AGENT looks like too. The same two turns had already passed by hand in
    `expense_agent_v4.main()` minutes earlier, and that contradiction was the
    only reason the harness got suspected before the prompt did.

    > **Reset per CASE, never per TURN.** A multi-turn harness has two clocks,
    > and mixing them up produces a failure that reads as a model problem.
    """
    expense_store.reset(seeded=True)

    total = 0
    passed = 0
    ok = True

    # Built once per case, cleared once, then reused across the case's turns.
    # A dict rather than one session because M3 deliberately uses two ids.
    sessions: dict[str, Session] = {}

    async def session_for(name: str) -> Session:
        if name not in sessions:
            fresh = make_session(name)
            await fresh.clear_session()
            sessions[name] = fresh
        return sessions[name]

    for index, turn in enumerate(case.turns, start=1):
        if turn.before is not None:
            turn.before()
            print("    [the world changed between turns]")

        session = None
        if case.use_session:
            session = await session_for(turn.session_id or f"case_{case.number}")

        run = await run_expense_agent(turn.prompt, user=turn.user, session=session)
        checks = turn.verify(run)

        print(f"    TURN {index} [{turn.user.name}]: {turn.prompt}")
        for label, result in checks:
            total += 1
            passed += result
            ok &= result
            print(f"      {'PASS' if result else 'FAIL'}  {label}")
        print(
            f"      branch={run.branch}  turns={run.iterations}  "
            f"items={run.session_items}  in_tok={run.input_tokens}"
        )
        if run.output_error:
            print(f"      OUTPUT ERROR: {run.output_error}")

        if index < len(case.turns):
            await asyncio.sleep(PAUSE_BETWEEN_TURNS)

    return passed, total, ok


async def main(wanted: set[int] | None = None) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)

    cases = [c for c in CASES if wanted is None or c.number in wanted]
    total_checks = 0
    passed_checks = 0
    failed: list[int] = []

    print(f"Spendly Lite v4 - multi-turn dataset ({len(cases)} of {len(CASES)} cases)")
    print("Every case here is a question a single-turn dataset cannot ask.")
    print(f"Expect roughly {len(cases) * 2.2:.0f} minutes.\n")

    for index, case in enumerate(cases):
        print(f"CASE M{case.number}: {case.name}")
        print(f"  expect: {case.expectation}")
        passed, total, ok = await run_case(case)
        total_checks += total
        passed_checks += passed
        if not ok:
            failed.append(case.number)
        print()
        if index < len(cases) - 1:
            await asyncio.sleep(PAUSE_BETWEEN_CASES)

    print("=" * 72)
    print(f"{passed_checks}/{total_checks} checks passed")
    if failed:
        print(f"FAILED CASES: {failed}")
        print()
        print("Check the failure SHAPE first. `branch=none turns=0` with a waiting")
        print("line above it is the free-tier quota in costume, not a broken agent.")
        print("Re-run only those cases with --only after the quota resets, or switch")
        print("MODEL_NAME in .env for a fresh per-day bucket.")
    else:
        print("All cases passed.")
    return 0 if not failed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Grade Spendly Lite v4 on multi-turn behaviour.")
    parser.add_argument("--only", metavar="N", help="comma-separated case numbers, e.g. --only 1,4")
    args = parser.parse_args()
    selected = {int(n) for n in args.only.split(",")} if args.only else None
    raise SystemExit(asyncio.run(main(selected)))
