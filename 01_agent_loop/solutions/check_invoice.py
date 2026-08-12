"""
Chapter 1 Project solution — the check harness behind RUNS.md.

Five hand-written cases with expected behaviour, asserted automatically.
This is a golden dataset with 5 rows. Step 5 grows it to 50 and adds an
LLM judge for the cases where "correct" is a paragraph rather than a number.

Run:  uv run python 01_agent_loop/solutions/check_invoice.py

Note: each case is a real API round-trip, so the whole file costs ~5 runs.
On the Gemini free tier that is fine; be aware of it on a paid model.
"""

from __future__ import annotations

import sys
import time
from collections.abc import Callable
from dataclasses import dataclass

from invoice_agent import SYSTEM_PROMPT
from invoice_tools import TOOL_REGISTRY, TOOL_SCHEMAS
from loop import AgentRun, run_agent

PAUSE_BETWEEN_CASES = 30.0  # seconds — stay under the free-tier rate limit


def normalise(text: str) -> str:
    """Strip thousands separators so '107,493.75' and '107493.75' both match."""
    return text.replace(",", "").lower()


@dataclass
class Case:
    number: int
    prompt: str
    expectation: str
    verify: Callable[[AgentRun], list[tuple[str, bool]]]


def case_1(run: AgentRun) -> list[tuple[str, bool]]:
    answer = normalise(run.final_answer)
    return [
        ("total 107493.75 appears in the answer", "107493.7" in answer),
        ("lookup_rate called twice (two roles)", run.tool_names.count("lookup_rate") == 2),
        ("line_total called twice", run.tool_names.count("line_total") == 2),
        ("apply_discount was used", "apply_discount" in run.tool_names),
        ("apply_tax was used", "apply_tax" in run.tool_names),
        ("the invoice was saved", "save_invoice" in run.tool_names),
        ("at least 5 tool calls", len(run.tool_calls) >= 5),
        ("at least 3 iterations (real chaining)", run.iterations >= 3),
        ("budget not exhausted", not run.hit_max_iterations),
    ]


def case_2(run: AgentRun) -> list[tuple[str, bool]]:
    answer = normalise(run.final_answer)
    # NOTE: an early version of this check asserted `apply_discount` was never
    # called. The agent legitimately calls it with percent=0 — which is correct
    # behaviour, not a bug. Assert on the OUTCOME (nothing was deducted), not on
    # the exact path the model chose. Over-specified checks fail good agents.
    discount_calls = [tc for tc in run.tool_calls if tc.name == "apply_discount"]
    return [
        ("total 58800 appears in the answer", "58800" in answer),
        (
            "no money was actually discounted",
            all(float(tc.arguments.get("percent", 0)) == 0 for tc in discount_calls),
        ),
        ("tax was applied", "apply_tax" in run.tool_names),
        ("the invoice was saved", "save_invoice" in run.tool_names),
    ]


def case_3(run: AgentRun) -> list[tuple[str, bool]]:
    answer = run.final_answer.lower()
    # Two acceptable paths: the model calls lookup_rate and recovers from the
    # error, OR it reads the valid roles straight off the tool description and
    # refuses without spending a call. The second is cheaper and smarter — so
    # the check accepts either. What is NOT acceptable is inventing a rate.
    return [
        ("NO file was written", "save_invoice" not in run.tool_names),
        (
            "the reply names at least one valid role",
            any(role in answer for role in ("backend", "frontend", "devops", "consulting")),
        ),
        (
            "it says the role is invalid",
            any(
                phrase in answer
                for phrase in (
                    "not a valid",
                    "not on the rate card",
                    "no rate",
                    "cannot",
                    "can't",
                    "not available",
                )
            ),
        ),
        ("no rate was invented for welding", "line_total" not in run.tool_names),
    ]


def case_4(run: AgentRun) -> list[tuple[str, bool]]:
    answer = run.final_answer.lower()
    # Don't assert on "?" — a numbered list of required fields is a perfectly
    # good way to ask. Assert on what the agent must NOT do (invent + save) and
    # on the information it must request.
    return [
        ("NO file was written", "save_invoice" not in run.tool_names),
        ("no amounts were calculated from invented data", "line_total" not in run.tool_names),
        ("it asks for the hours", "hour" in answer),
        ("it asks for the client", "client" in answer),
    ]


def case_5(run: AgentRun) -> list[tuple[str, bool]]:
    return [
        (
            "line_total rejected the negative hours",
            any(tc.name == "line_total" and tc.errored for tc in run.tool_calls)
            or "line_total" not in run.tool_names,
        ),
        ("NO file was written", "save_invoice" not in run.tool_names),
        ("the agent explains the problem", bool(run.final_answer.strip())),
    ]


CASES: list[Case] = [
    Case(
        1,
        "I did 12 hours of backend work and 6.5 hours of UI design for Acme Corp "
        "this month. Apply the 10% loyalty discount and 5% tax. Save the invoice.",
        "Total 107,493.75, invoice saved",
        case_1,
    ),
    Case(
        2,
        "8 hours of devops for Beta Ltd, no discount, 5% tax. Save it.",
        "Total 58,800.00, invoice saved",
        case_2,
    ),
    Case(
        3,
        "I did 5 hours of underwater welding for Gamma Inc. Make the invoice.",
        "Helpful refusal listing valid roles, no file written",
        case_3,
    ),
    Case(4, "Make me an invoice.", "Asks for client, role and hours", case_4),
    Case(
        5,
        "Bill Delta Co for -3 hours of backend work.",
        "Rejects the negative hours, no file written",
        case_5,
    ),
]


def main() -> int:
    total_checks = 0
    total_passed = 0
    rows: list[str] = []

    for index, case in enumerate(CASES):
        # Free tier: ~15 requests/minute. One case is up to 8 requests, so pace
        # them. loop.py also retries 429s, but pausing is cheaper than backing off.
        if index > 0:
            time.sleep(PAUSE_BETWEEN_CASES)

        print("\n" + "=" * 72)
        print(f"CASE {case.number}: {case.prompt}")
        print(f"EXPECTED: {case.expectation}")
        print("=" * 72)

        run = run_agent(
            user_message=case.prompt,
            tool_registry=TOOL_REGISTRY,
            tool_schemas=TOOL_SCHEMAS,
            system_prompt=SYSTEM_PROMPT,
            verbose=False,
        )

        print(f"ANSWER  : {run.final_answer.strip()[:400]}")
        print(f"TOOLS   : {run.tool_names or 'none'}  |  iterations: {run.iterations}")

        checks = case.verify(run)
        passed = sum(1 for _, ok in checks if ok)
        for label, ok in checks:
            print(f"  [{'PASS' if ok else 'FAIL'}] {label}")

        total_checks += len(checks)
        total_passed += passed
        rows.append(
            f"| {case.number} | {passed}/{len(checks)} | "
            f"{', '.join(run.tool_names) or 'none'} | {run.iterations} | "
            f"{'PASS' if passed == len(checks) else 'FAIL'} |"
        )

    print("\n" + "=" * 72)
    print("| # | Checks | Tools called | Iterations | Pass? |")
    print("|---|--------|--------------|------------|-------|")
    for row in rows:
        print(row)
    print(f"\n{total_passed}/{total_checks} checks passed across {len(CASES)} cases.")

    return 0 if total_passed == total_checks else 1


if __name__ == "__main__":
    sys.exit(main())
