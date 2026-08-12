"""
Chapter 2, Concept 2 — break the Chapter 1 agent on purpose.

    uv run python 02_typed_tools/from_scratch/break_it.py

No API key, no network, no cost. Every "tool call" below is a real payload a
model has actually emitted at some point: a tool name and an arguments STRING.
We dispatch them exactly the way Chapter 1's loop did, and watch what happens.

Chapter 1's dispatch, verbatim:

    tool_args = json.loads(raw_args)
    tool_fn = TOOL_REGISTRY[tool_name]
    tool_result = tool_fn(**tool_args)

Three lines. Read them as a security question rather than a plumbing question:
`**tool_args` unpacks whatever the model wrote straight into your function's
parameters. There is nothing between a token predictor and your code.

Rank the six cases below from "most dangerous" to "least dangerous" BEFORE you
run the file. Most people get the ranking wrong, and the way they get it wrong
is the point of this chapter.
"""

from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any

# -----------------------------------------------------------------------------
# Chapter 1's tools, copied here unchanged. Plain functions, no guards.
# -----------------------------------------------------------------------------


def add(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


def divide(a: float, b: float) -> float:
    """Return the division of two numbers."""
    return a / b


def log_expense(vendor: str, amount: float, category: str) -> str:
    """Pretend to write an expense to storage."""
    return f"WROTE TO LEDGER -> {vendor} | {amount} | {category}"


REGISTRY: dict[str, Callable[..., Any]] = {
    "add": add,
    "divide": divide,
    "log_expense": log_expense,
}


# -----------------------------------------------------------------------------
# Chapter 1's dispatch, also unchanged. This is the code under test.
# -----------------------------------------------------------------------------


def chapter_1_dispatch(tool_name: str, raw_arguments: str) -> str:
    """Exactly what `01_agent_loop/from_scratch/agent.py` does with a tool call."""
    try:
        tool_args = json.loads(raw_arguments) if raw_arguments else {}
    except json.JSONDecodeError as exc:
        return f"ERROR: bad JSON: {exc}"

    try:
        result = REGISTRY[tool_name](**tool_args)
        return result if isinstance(result, str) else json.dumps(result)
    except KeyError:
        return f"ERROR: unknown tool '{tool_name}'"
    except Exception as exc:
        return f"ERROR: {type(exc).__name__}: {exc}"


# -----------------------------------------------------------------------------
# Six tool calls a model can plausibly produce.
# -----------------------------------------------------------------------------

ATTACKS: list[tuple[str, str, str, str]] = [
    (
        "Wrong type",
        "add",
        '{"a": "fifty", "b": 3}',
        "The user said 'fifty' and the model passed the word through.",
    ),
    (
        "Missing argument",
        "add",
        '{"a": 5}',
        "The model forgot half the call.",
    ),
    (
        "Invented argument",
        "add",
        '{"a": 5, "b": 3, "precision": 2}',
        "The model wanted rounding, so it made up a parameter.",
    ),
    (
        "Malformed JSON",
        "add",
        '{"a": 5, "b": }',
        "Generation was truncated mid-object.",
    ),
    (
        "Out-of-set value",
        "log_expense",
        '{"vendor": "Al-Falah", "amount": 2000, "category": "astrology"}',
        "The category is not one of the ten Spendly allows.",
    ),
    (
        "Numeric strings",
        "add",
        '{"a": "5", "b": "3"}',
        "The model quoted the numbers. Watch this one closely.",
    ),
]


def main() -> None:
    print("Chapter 1 dispatch, six hostile payloads\n" + "=" * 72)

    for label, name, raw, note in ATTACKS:
        result = chapter_1_dispatch(name, raw)
        print(f"\n[{label}]  {note}")
        print(f"  model sent : {name}({raw})")
        print(f"  model saw  : {result}")

    print("\n" + "=" * 72)
    print(
        "\nFour of those six raised. Two did not, and the two that did not are\n"
        "the dangerous ones.\n"
        "\n"
        '  add(a="5", b="3")           ->  "53"\n'
        '  log_expense(...astrology")  ->  WROTE TO LEDGER\n'
        "\n"
        "No exception. No error string. No warning anywhere. Python concatenated\n"
        "two strings and the loop cheerfully handed '53' back to the model as the\n"
        "sum of five and three. Meanwhile a category that does not exist was\n"
        "written to permanent storage, and the model was told it succeeded.\n"
        "\n"
        "That is why 'my tools raise exceptions when things go wrong' is not a\n"
        "validation strategy. The failures that hurt are the ones that do not\n"
        "raise. A crash is loud, local, and debuggable. A silently wrong value\n"
        "propagates through the rest of the conversation and arrives at the user\n"
        "wearing a full sentence of justification. A silently wrong WRITE is still\n"
        "there tomorrow.\n"
        "\n"
        "Now look at the four that did raise and ask the second question of this\n"
        "chapter:\n"
        "could the MODEL fix the problem, given what we told it?\n"
        "\n"
        "  'ERROR: TypeError: unsupported operand type(s) for +: str and int'\n"
        "\n"
        "That message names a Python internal, does not name the tool, does not\n"
        "say which argument was wrong, does not say what the right shape is, and\n"
        "does not say whether anything was already written to storage. It is a\n"
        "message for a developer reading a traceback. There is no developer here.\n"
        "The only reader is a model deciding what to do next."
    )


if __name__ == "__main__":
    main()
