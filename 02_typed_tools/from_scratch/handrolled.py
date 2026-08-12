"""
Chapter 2, Concept 3 — validate one tool call by hand, and count the cost.

    uv run python 02_typed_tools/from_scratch/handrolled.py

This file is deliberately tedious. Do not skim it; the tedium IS the argument.
Write it once, feel the length, and you will never again wonder why every
serious agent framework has a validation layer.

Rules we want to enforce for ONE tool, `log_expense(vendor, amount, category)`:

    1. the payload is an object, not a list or a bare value
    2. no unknown keys (the model must not invent parameters)
    3. `vendor` is present, is a string, is not blank
    4. `amount` is present, is a number, is not a bool, is greater than zero
    5. `category` is present, is a string, is one of ten allowed values
    6. `expense_date` is optional, and if present matches YYYY-MM-DD
    7. every failure message is written for the MODEL, not for a developer

Seven rules. One tool. Now scroll to the bottom and read the line count.
"""

from __future__ import annotations

import re
from typing import Any

CATEGORIES: tuple[str, ...] = (
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
)

ALLOWED_KEYS = {"vendor", "amount", "category", "expense_date"}
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")


class ToolError(Exception):
    """A failure the model is meant to read and recover from."""


def validate_log_expense(payload: Any) -> dict[str, Any]:
    """
    Check every rule above and return clean, typed arguments.

    Returning a NEW dict rather than mutating the input matters: the caller
    should be unable to accidentally use the unvalidated version. "Parse, don't
    validate" — the output type proves the check happened.
    """
    # Rule 1 — shape
    if not isinstance(payload, dict):
        raise ToolError(
            f"Arguments for 'log_expense' must be a JSON object, got {type(payload).__name__}."
        )

    # Rule 2 — no invented keys
    unknown = set(payload) - ALLOWED_KEYS
    if unknown:
        raise ToolError(
            f"'log_expense' does not accept {sorted(unknown)}. Valid arguments "
            f"are {sorted(ALLOWED_KEYS)}."
        )

    # Rule 3 — vendor
    if "vendor" not in payload:
        raise ToolError("'vendor' is required. Ask the user where the money was spent.")
    vendor = payload["vendor"]
    if not isinstance(vendor, str):
        raise ToolError(f"'vendor' must be a string, got {type(vendor).__name__}.")
    vendor = vendor.strip()
    if not vendor:
        raise ToolError("'vendor' was blank. Ask the user where the money was spent.")

    # Rule 4 — amount. Note the bool check: in Python, True is an int, so
    # `isinstance(True, (int, float))` passes and you would log an expense of 1.
    if "amount" not in payload:
        raise ToolError("'amount' is required. Ask the user how much they spent.")
    amount = payload["amount"]
    if isinstance(amount, bool) or not isinstance(amount, (int, float)):
        raise ToolError(
            f"'amount' must be a number, got {type(amount).__name__} "
            f"({amount!r}). Send it as a JSON number, not text."
        )
    amount = float(amount)
    if amount <= 0:
        raise ToolError(
            f"'amount' must be greater than zero, got {amount}. Do NOT flip the "
            f"sign yourself. Ask the user to confirm what they actually spent."
        )

    # Rule 5 — category, case-insensitively resolved against a closed set
    if "category" not in payload:
        raise ToolError(f"'category' is required. Valid categories: {', '.join(CATEGORIES)}.")
    category = payload["category"]
    if not isinstance(category, str):
        raise ToolError(f"'category' must be a string, got {type(category).__name__}.")
    resolved = next((c for c in CATEGORIES if c.lower() == category.strip().lower()), None)
    if resolved is None:
        raise ToolError(
            f"'{category}' is not a valid category. Pick one of: "
            f"{', '.join(CATEGORIES)}. Do not invent a category and do not log "
            f"the expense until the user chooses."
        )

    # Rule 6 — optional date
    expense_date = payload.get("expense_date", "")
    if expense_date:
        if not isinstance(expense_date, str):
            raise ToolError(f"'expense_date' must be a string, got {type(expense_date).__name__}.")
        if not DATE_PATTERN.match(expense_date):
            raise ToolError(f"'expense_date' must look like YYYY-MM-DD, got '{expense_date}'.")

    return {
        "vendor": vendor,
        "amount": amount,
        "category": resolved,
        "expense_date": expense_date,
    }


# -----------------------------------------------------------------------------
# Proof that it works, and the bill.
# -----------------------------------------------------------------------------

PAYLOADS: list[Any] = [
    {"vendor": "KFC", "amount": 1500, "category": "food & dining"},
    {"vendor": "KFC", "amount": "fifty", "category": "Food & Dining"},
    {"vendor": "KFC", "amount": True, "category": "Food & Dining"},
    {"vendor": "  ", "amount": 1500, "category": "Food & Dining"},
    {"vendor": "Al-Falah", "amount": 2000, "category": "astrology"},
    {"vendor": "KFC", "amount": 1500, "category": "Food & Dining", "tip": 100},
    {"vendor": "KFC", "amount": -450, "category": "Food & Dining"},
    ["KFC", 1500, "Food & Dining"],
]


def main() -> None:
    print("Hand-rolled validation for ONE tool\n" + "=" * 72)
    for payload in PAYLOADS:
        try:
            clean = validate_log_expense(payload)
            print(f"\n  OK   {payload}\n       -> {clean}")
        except ToolError as exc:
            print(f"\n  FAIL {payload}\n       -> {exc}")

    print("\n" + "=" * 72)
    print(
        "\nEvery rejection above is correct, including the two that Chapter 1's\n"
        "dispatch let through silently. So the gauntlet WORKS. The problem is\n"
        "not correctness, it is arithmetic:\n"
        "\n"
        "  ~85 lines of validation, for ONE tool with THREE arguments.\n"
        "  Spendly Lite has seven tools.\n"
        "  A real agent has thirty.\n"
        "\n"
        "And the cost is worse than the line count suggests, because this code\n"
        "duplicates knowledge that already exists two feet away:\n"
        "\n"
        "  - the signature already says amount is a float\n"
        "  - the JSON schema you hand-wrote in Chapter 1 already said 'number'\n"
        "  - this function says it a third time, in a third syntax\n"
        "\n"
        "Three copies of one fact, kept in sync by hope. The first time someone\n"
        "adds a `notes` parameter, they will update one or two of the three.\n"
        "\n"
        "So the goal is not 'add validation'. You just did that, and it is not\n"
        "sustainable. The goal is ONE declaration that produces all three:\n"
        "the signature, the schema the model reads, and the check on the way in.\n"
        "\n"
        "That is the next concept. Open `typed_tool.py`."
    )


if __name__ == "__main__":
    main()
