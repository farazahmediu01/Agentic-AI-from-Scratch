"""
Spendly Lite — the storage layer.

A JSON file, deliberately. You can open it in a text editor and see exactly what
the agent wrote, which matters more in Chapter 1 than durability does. The
persistence chapter replaces this with SQLite; the tools above it will not change.

Nothing in this file is agent-specific. That separation is the point: an agent
tool should be a thin wrapper over business logic you could call from a web app,
a cron job, or a test.
"""

from __future__ import annotations

import json
from datetime import date, datetime
from pathlib import Path
from typing import TypedDict

STORE_PATH = Path(__file__).parent / "data" / "expenses.json"

# Spendly's ten categories. A closed set is what makes a spending report
# possible at all — free-text categories are how expense trackers die.
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
