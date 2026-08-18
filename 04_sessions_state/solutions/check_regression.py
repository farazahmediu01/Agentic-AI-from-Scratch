"""
The regression rule, as a command you can run.

    uv run python 04_sessions_state/solutions/check_regression.py
    uv run python 04_sessions_state/solutions/check_regression.py --only 1,6

`CLAUDE.md` says every prior chapter's golden-dataset cases must still pass. Up
to now that was enforced by re-running the previous chapter's harness against the
previous chapter's agent -- which proves the OLD code still works and says
nothing at all about the new code.

This file closes that hole. It imports Chapter 3's nine cases, verbatim, and
pushes them through **Chapter 4's** agent:

    from check_expenses import CASES        <- Chapter 3's dataset, unmodified
    from expense_agent_v4 import run_expense_agent   <- this chapter's agent

Not one case was copied, edited or re-typed. If a Chapter 3 case is wrong, it is
wrong in exactly one place.

WHY THIS WAS ALMOST FREE, AND THE DESIGN LESSON IN THAT
--------------------------------------------------------
Chapter 3's harness declared what it needed from a run as a `Protocol` -- a
structural type listing `branch`, `executed_names`, `reply` and so on -- rather
than importing v3's concrete `SdkRun` class. At the time that looked like extra
ceremony for no benefit; nothing else implemented it.

One chapter later it is why this file is forty lines instead of a fork of the
dataset. `SdkRun` in v4 grew two new fields and still satisfies the Protocol, so
Chapter 3's checks accept it without knowing it exists.

> **The generalisation, which is worth more than the file:** depend on the shape
> you need, not the class you happen to have. You cannot predict which of your
> types will be replaced, but you can make the replacement cheap.

WHAT PASSING HERE MEANS, AND WHAT IT DOES NOT
----------------------------------------------
It means adding sessions and a context object did not change single-turn
behaviour. It does NOT mean Chapter 4 is correct -- nothing here runs more than
one turn. `check_multiturn.py` is the other half, and neither is sufficient alone.
"""

from __future__ import annotations

import argparse
import asyncio
import io
import sys

import _bootstrap  # noqa: F401  -- must precede every spine import
import expense_store
from check_expenses import CASES, PAUSE_BETWEEN_CASES
from expense_agent_v4 import run_expense_agent
from spendly_context import default_user


async def main(wanted: set[int] | None = None) -> int:
    if isinstance(sys.stdout, io.TextIOWrapper):
        sys.stdout.reconfigure(line_buffering=True)

    cases = [c for c in CASES if wanted is None or c.number in wanted]
    total = 0
    passed = 0
    failed: list[int] = []

    print(f"Chapter 3's dataset, run against Chapter 4's agent ({len(cases)} cases)")
    print("No session is attached: these are the single-turn cases, unchanged.")
    print(f"Expect roughly {len(cases) * 1.5:.0f} minutes.\n")

    for index, case in enumerate(cases):
        expense_store.reset(seeded=True)
        print(f"CASE {case.number}: {case.prompt}")
        print(f"  expect: {case.expectation}")

        # session=None on purpose. Chapter 3's cases assume a fresh agent every
        # time, and attaching a session would change what they are testing -- the
        # regression run must reproduce the OLD conditions, not the new ones.
        run = await run_expense_agent(case.prompt, user=default_user(), session=None)

        case_ok = True
        for label, ok in case.verify(run):
            total += 1
            passed += ok
            case_ok &= ok
            print(f"    {'PASS' if ok else 'FAIL'}  {label}")

        if not case_ok:
            failed.append(case.number)
        print(f"  branch={run.branch}  turns={run.iterations}  rejected={run.rejected_count}")
        if run.output_error:
            print(f"  OUTPUT ERROR: {run.output_error}")
        print()

        if index < len(cases) - 1:
            await asyncio.sleep(PAUSE_BETWEEN_CASES)

    print("=" * 72)
    print(f"{passed}/{total} checks passed")
    if failed:
        print(f"FAILED CASES: {failed}")
        print()
        print("A failure here means CHAPTER 4 BROKE CHAPTER 3, which is the one")
        print("outcome the regression rule exists to catch. Diagnose the shape")
        print("first -- `branch=none turns=0` is quota, not a regression.")
    else:
        print("All cases passed. Chapter 3's behaviour survived Chapter 4.")
    return 0 if not failed else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Chapter 3's dataset against v4.")
    parser.add_argument("--only", metavar="N", help="comma-separated case numbers, e.g. --only 1,6")
    args = parser.parse_args()
    selected = {int(n) for n in args.only.split(",")} if args.only else None
    raise SystemExit(asyncio.run(main(selected)))
