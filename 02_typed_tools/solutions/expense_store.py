"""
Spendly Lite — the storage layer. Carried forward from Chapter 1, with ONE
change, and the fact that there is only one is the point.

Diff it against `../../01_agent_loop/solutions/expense_store.py`:

    +Category = Literal["Food & Dining", ...]
    -CATEGORIES: tuple[str, ...] = ("Food & Dining", ...)
    +CATEGORIES: tuple[str, ...] = get_args(Category)

The list of categories did not change. What changed is that it is now a TYPE as
well as a value, so it can appear in a function signature — and from there it
flows automatically into the JSON Schema the model reads and into the check that
runs before any tool body executes.

Chapter 1 had this same closed set and could only describe it in English, inside
a `"description"` string, and hope. That hope is what Chapter 2 removes.

Everything below the type is untouched. A validation layer that forced you to
rewrite your storage would be a bad validation layer.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import Literal, TypedDict, get_args

STORE_PATH = Path(__file__).parent / "data" / "expenses.json"

# Spendly's ten categories, as a type. A closed set is what makes a spending
# report possible at all — free-text categories are how expense trackers die.
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

# One source of truth: the runtime tuple is DERIVED from the type, not typed out
# a second time. Two hand-maintained copies of the same list is exactly the kind
# of drift this chapter exists to delete.
CATEGORIES: tuple[str, ...] = get_args(Category)

# Monthly budget per category, in PKR.
MONTHLY_BUDGETS: dict[str, float] = {
    "Food & Dining": 25000.0,
    "Transportation": 12000.0,
    "Shopping": 15000.0,
    "Bills & Utilities": 18000.0,
    "Entertainment": 8000.0,
    "Health & Medical": 10000.0,
    "Education": 20000.0,
    "Groceries": 30000.0,
    "Office Supplies": 5000.0,
    "Miscellaneous": 6000.0,
}


class Expense(TypedDict):
    id: str
    date: str
    vendor: str
    amount: float
    category: str
    notes: str


def _read() -> list[Expense]:
    if not STORE_PATH.exists():
        return []
    return json.loads(STORE_PATH.read_text(encoding="utf-8"))


def _write(rows: list[Expense]) -> None:
    STORE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STORE_PATH.write_text(json.dumps(rows, indent=2), encoding="utf-8")


def append(expense: Expense) -> None:
    rows = _read()
    rows.append(expense)
    _write(rows)


def all_expenses() -> list[Expense]:
    return _read()


def month_of(iso_date: str) -> str:
    """'2026-08-12' -> '2026-08'."""
    return iso_date[:7]


def current_month() -> str:
    return date.today().strftime("%Y-%m")


def next_id() -> str:
    return f"EXP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{len(_read()) + 1:03d}"


def reset(seeded: bool = True) -> None:
    """
    Wipe the store, optionally seeding a known month of spending.

    The check harness calls this before every case. An eval that depends on
    leftover state from the previous run is not an eval — it's a coin flip.
    """
    rows: list[Expense] = []
    if seeded:
        month = current_month()
        rows = [
            {
                "id": "EXP-SEED-001",
                "date": f"{month}-02",
                "vendor": "Cafe Zouk",
                "amount": 3200.0,
                "category": "Food & Dining",
                "notes": "seed",
            },
            {
                "id": "EXP-SEED-002",
                "date": f"{month}-05",
                "vendor": "Student Biryani",
                "amount": 1800.0,
                "category": "Food & Dining",
                "notes": "seed",
            },
            {
                "id": "EXP-SEED-003",
                "date": f"{month}-08",
                "vendor": "Broadway Pizza",
                "amount": 2500.0,
                "category": "Food & Dining",
                "notes": "seed",
            },
            {
                "id": "EXP-SEED-004",
                "date": f"{month}-03",
                "vendor": "Careem",
                "amount": 900.0,
                "category": "Transportation",
                "notes": "seed",
            },
        ]
    _write(rows)


# Seeded Food & Dining total for the current month: 3200 + 1800 + 2500 = 7500
SEEDED_FOOD_TOTAL = 7500.0
