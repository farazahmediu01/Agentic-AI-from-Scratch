"""
Spendly Lite v1 — the tools, hand-rolled (Layer 2).

Seven tools, a registry, and seven JSON schemas written by hand. Read the
schemas and notice how much typing they cost. In `expense_agent_sdk.py` all of
it disappears into `@function_tool` — but you should feel the cost first.

Two design rules are visible throughout, and both matter more than the code:

  1. Every `raise` is written for the MODEL to read and act on. Compare
     "KeyError: 'astrology'" with what `validate_category` actually raises.
  2. Only ONE tool changes the world (`log_expense`). Everything else is a
     read. That asymmetry is what the Trust chapters are about.
"""

from __future__ import annotations

from collections.abc import Callable
from datetime import date

from openai.types.chat import ChatCompletionToolParam

from expense_store import (
    CATEGORIES,
    MONTHLY_BUDGETS,
    Expense,
    all_expenses,
    append,
    current_month,
    month_of,
    next_id,
)


def _valid_category(category: str) -> str:
    """Resolve a category case-insensitively, or raise a model-readable error."""
    for known in CATEGORIES:
        if known.lower() == category.strip().lower():
            return known
    raise ValueError(
        f"'{category}' is not a valid category. Tell the user which categories exist "
        f"and ask them to pick one: {', '.join(CATEGORIES)}. Do not invent a category "
        f"and do not log the expense until they choose."
    )


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------


def get_today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().isoformat()


def log_expense(vendor: str, amount: float, category: str, expense_date: str = "") -> str:
    """Record one expense. The only tool here with a side effect."""
    if amount <= 0:
        raise ValueError(
            f"Amount must be greater than zero (got {amount}). Do NOT correct this "
            f"value yourself — ask the user to confirm what they actually spent."
        )
    if not vendor.strip():
        raise ValueError("Vendor is required. Ask the user where they spent the money.")

    resolved = _valid_category(category)
    when = expense_date.strip() or get_today()

    expense: Expense = {
        "id": next_id(),
        "date": when,
        "vendor": vendor.strip(),
        "amount": float(amount),
        "category": resolved,
        "notes": "",
    }
    append(expense)
    return (
        f"Logged {expense['id']}: PKR {amount:,.2f} at {expense['vendor']} ({resolved}) on {when}"
    )


def month_total(category: str, month: str = "") -> float:
    """Total spend for one category in one month (YYYY-MM). Defaults to this month."""
    resolved = _valid_category(category)
    target = month.strip() or current_month()
    return sum(
        row["amount"]
        for row in all_expenses()
        if row["category"] == resolved and month_of(row["date"]) == target
    )


def get_budget(category: str) -> float:
    """Return the monthly budget in PKR for a category."""
    return MONTHLY_BUDGETS[_valid_category(category)]


def subtract(a: float, b: float) -> float:
    """Subtract b from a. Use it to compute budget remaining."""
    return a - b


def list_recent(limit: int = 5) -> str:
    """List the most recently recorded expenses, newest last."""
    rows = all_expenses()[-limit:]
    if not rows:
        return "No expenses recorded yet."
    return "\n".join(
        f"{r['date']}  {r['vendor']:<20} PKR {r['amount']:>10,.2f}  {r['category']}" for r in rows
    )


def list_categories() -> str:
    """List every valid expense category."""
    return ", ".join(CATEGORIES)


TOOL_REGISTRY: dict[str, Callable] = {
    "get_today": get_today,
    "log_expense": log_expense,
    "month_total": month_total,
    "get_budget": get_budget,
    "subtract": subtract,
    "list_recent": list_recent,
    "list_categories": list_categories,
}


_CATEGORY_DESC = f"One of exactly these categories: {', '.join(CATEGORIES)}"


TOOL_SCHEMAS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_today",
            "description": "Get today's date as YYYY-MM-DD. Takes no arguments.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "log_expense",
            "description": (
                "Record one expense in the user's ledger. Call this ONLY when you know "
                "the vendor, the amount, and a valid category. This writes to storage — "
                "never call it with guessed or corrected values."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vendor": {"type": "string", "description": "Where the money was spent"},
                    "amount": {"type": "number", "description": "Amount in PKR, must be > 0"},
                    "category": {"type": "string", "description": _CATEGORY_DESC},
                    "expense_date": {
                        "type": "string",
                        "description": "Date as YYYY-MM-DD. Omit to use today.",
                    },
                },
                "required": ["vendor", "amount", "category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "month_total",
            "description": (
                "Total amount already spent in one category during one month. "
                "Use it to answer 'how much have I spent on X' and to check budgets."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": _CATEGORY_DESC},
                    "month": {
                        "type": "string",
                        "description": "Month as YYYY-MM. Omit for the current month.",
                    },
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_budget",
            "description": "Get the monthly budget in PKR for one category.",
            "parameters": {
                "type": "object",
                "properties": {
                    "category": {"type": "string", "description": _CATEGORY_DESC},
                },
                "required": ["category"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "subtract",
            "description": (
                "Subtract b from a. Use it to compute budget remaining: "
                "subtract(budget, amount_spent)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "The number to subtract from"},
                    "b": {"type": "number", "description": "The number to subtract"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_recent",
            "description": "Show the most recent expenses the user recorded.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "How many to show, default 5"},
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_categories",
            "description": (
                "List every valid expense category. Call this when the user's category "
                "is unclear or invalid, so you can offer them the real options."
            ),
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
]
