"""
Exercise 5 solution — assertion checks over a structured AgentRun.

This is the seed of Step 5's eval harness. The important idea: we assert on
*what the agent did*, not only on what it said. An agent that returns the right
number by guessing instead of calling the tool is a bug that will bite you the
first time the numbers get harder.

Run:  uv run python 01_agent_loop/solutions/check_agent.py
"""

from __future__ import annotations

import sys

from loop import AgentRun, run_agent
from unit_tools import TOOL_REGISTRY, TOOL_SCHEMAS

SYSTEM_PROMPT = (
    "You are a precise unit-conversion assistant. Never convert in your head — "
    "always call the matching tool. Stop calling tools once you have the answer."
)


def check(label: str, condition: bool, detail: str = "") -> bool:
    mark = "PASS" if condition else "FAIL"
    print(f"  [{mark}] {label}" + (f" — {detail}" if detail and not condition else ""))
    return condition


def main() -> int:
    run: AgentRun = run_agent(
        user_message="How many miles is 340 km?",
        tool_registry=TOOL_REGISTRY,
        tool_schemas=TOOL_SCHEMAS,
        system_prompt=SYSTEM_PROMPT,
        verbose=False,
    )

    print(f"\nFinal answer: {run.final_answer}\n")
    print("Checks:")

    results = [
        check(
            "the km_to_miles tool was used",
            "km_to_miles" in run.tool_names,
            f"tools actually used: {run.tool_names}",
        ),
        check(
            "finished within 3 iterations",
            run.iterations <= 3,
            f"took {run.iterations}",
        ),
        check(
            "did not exhaust the iteration budget",
            not run.hit_max_iterations,
        ),
        check(
            "the answer contains 211",
            "211" in run.final_answer,
            f"got: {run.final_answer!r}",
        ),
        check(
            "no tool errored",
            run.error_count == 0,
            f"{run.error_count} tool error(s)",
        ),
    ]

    passed = sum(results)
    print(f"\n{passed}/{len(results)} checks passed.")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
