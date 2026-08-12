"""
Spendly Lite v2 — the tools, under contract.

Open `../../01_agent_loop/solutions/expense_tools.py` beside this file. Same
seven tools, same behaviour, same storage. That file is 245 lines. This one is
about half, and the half that vanished was the hand-written JSON Schema.

But the line count is the boring part. Read the three type aliases at the top,
then count the `if` statements in `log_expense`.

  Chapter 1's log_expense body:      3 hand-written guards + a resolver
  Chapter 2's log_expense body:      1 hand-written guard

The two that disappeared did not become someone else's problem. They moved INTO
THE SIGNATURE, where they do three jobs at once instead of one:

    amount: Amount            ->  "exclusiveMinimum": 0 in the schema the model reads
                              ->  a check that runs before the body
                              ->  a fact pyright can see at edit time

The one guard that stayed is the interesting one. Read `log_expense` and ask
why it could not move.
"""

from __future__ import annotations

from datetime import date
from typing import Annotated, Any

from pydantic import BeforeValidator, Field, StringConstraints

from chapter import Tool, ToolError, tool
from expense_store import (
    CATEGORIES,
    MONTHLY_BUDGETS,
    Category,
    Expense,
    all_expenses,
    append,
    current_month,
    month_of,
    next_id,
)

# -----------------------------------------------------------------------------
# The vocabulary of this agent, declared once.
#
# Naming these is not decoration. `vendor: Vendor` reads as a domain concept;
# `vendor: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]`
# reads as plumbing, and a signature made of plumbing is unreadable at seven
# arguments. Give constraints a name and reuse it.
# -----------------------------------------------------------------------------

Vendor = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
    Field(description="Where the money was spent, e.g. 'KFC' or 'Careem'"),
]


def _reject_bool(value: Any) -> Any:
    """
    Refuse `true`/`false` where a number belongs.

    This validator exists because a test caught a real bug, and the bug is one
    every Python codebase eventually meets:

        >>> class M(BaseModel):
        ...     x: float
        >>> M(x=True)
        x=1.0

    `bool` is a subclass of `int` in Python, so `True` is a perfectly valid
    number as far as Pydantic's default (lax) mode is concerned. A model that
    answers `{"amount": true}` -- and they do, when the user says "yes, log it"
    -- would have written an expense of PKR 1.00 to the ledger.

    The lesson is not "Pydantic is wrong". Lax coercion is what makes
    `"1500"` -> `1500.0` work, and we want that. The lesson is that a validation
    library has DEFAULTS, the defaults encode somebody's judgement, and reading
    them is part of using the tool. This is the same point the SDK's error-text
    default makes in `with_sdk/agent_sdk.py`, one layer down.

    `BeforeValidator` runs ahead of the type coercion, which is the only place
    this check can live -- by the time float parsing has happened, `True` is
    already `1.0` and indistinguishable from a real amount.
    """
    if isinstance(value, bool):
        raise ValueError("must be a number, not true/false")
    return value


# `gt=0` is the entire negative-amount defence from Chapter 1, expressed once.
# In Chapter 1 this rule lived in an `if` inside the function AND in an English
# sentence inside the schema, and only the `if` was enforced.
Amount = Annotated[
    float,
    BeforeValidator(_reject_bool),
    Field(gt=0, description="Amount in PKR. Must be greater than zero."),
]

# A wrinkle worth knowing rather than working around: this argument is optional
# AND format-constrained, and those two pull in opposite directions. The default
# is "" — which does not match a date pattern. So the pattern has to admit the
# empty string explicitly. The alternative is `str | None = None`, which is
# cleaner Python but emits an `anyOf` schema that some providers handle poorly.
# Both are defensible; what is not defensible is discovering the conflict in
# production because you never tried the default value.
IsoDate = Annotated[
    str,
    Field(
        pattern=r"^(\d{4}-\d{2}-\d{2})?$",
        description="Date as YYYY-MM-DD. Omit or send an empty string for today.",
    ),
]

Month = Annotated[
    str,
    Field(
        pattern=r"^(\d{4}-\d{2})?$",
        description="Month as YYYY-MM. Omit or send an empty string for the current month.",
    ),
]

Limit = Annotated[int, Field(ge=1, le=50, description="How many rows to show, 1 to 50")]


# -----------------------------------------------------------------------------
# Tools
# -----------------------------------------------------------------------------


@tool
def get_today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return date.today().isoformat()


@tool
def log_expense(
    vendor: Vendor,
    amount: Amount,
    category: Category,
    expense_date: IsoDate = "",
) -> str:
    """
    Record one expense in the user's ledger.

    This is the only tool here that changes anything. Call it only when the
    vendor, the amount and the category are all known. Never guess a value the
    user did not give you.
    """
    when = expense_date or get_today.fn()

    # THE GUARD THAT COULD NOT MOVE.
    #
    # "not in the future" is not a property of a string — it is a comparison
    # between this argument and the clock, evaluated at call time. No JSON Schema
    # can express it, so no amount of typing removes it.
    #
    # That is the honest boundary of this chapter. Types hold shape, range and
    # membership. They do not hold rules that depend on the world: today's date,
    # the account balance, whether this user is allowed to spend. Those stay
    # yours, they belong in the body, and they raise ToolError so the model can
    # still recover from them.
    if when > date.today().isoformat():
        raise ToolError(
            f"'{when}' is in the future. Expenses are recorded after they happen. "
            f"Ask the user for the real date, or omit expense_date to use today."
        )

    expense: Expense = {
        "id": next_id(),
        "date": when,
        "vendor": vendor,
        "amount": amount,
        "category": category,
        "notes": "",
    }
    append(expense)
    return f"Logged {expense['id']}: PKR {amount:,.2f} at {vendor} ({category}) on {when}"


@tool
def month_total(category: Category, month: Month = "") -> float:
    """
    Total amount already spent in one category during one month.

    Use it to answer "how much have I spent on X" and to check budgets.
    """
    target = month or current_month()
    return sum(
        row["amount"]
        for row in all_expenses()
        if row["category"] == category and month_of(row["date"]) == target
    )


@tool
def get_budget(category: Category) -> float:
    """Get the monthly budget in PKR for one category."""
    return MONTHLY_BUDGETS[category]


@tool
def subtract(a: float, b: float) -> float:
    """Subtract b from a. Use it to compute budget remaining: subtract(budget, spent)."""
    return a - b


@tool
def list_recent(limit: Limit = 5) -> str:
    """List the most recently recorded expenses, newest last."""
    rows = all_expenses()[-limit:]
    if not rows:
        return "No expenses recorded yet."
    return "\n".join(
        f"{r['date']}  {r['vendor']:<20} PKR {r['amount']:>10,.2f}  {r['category']}" for r in rows
    )


@tool
def list_categories() -> str:
    """
    List every valid expense category.

    Still here, and still worth calling, even though the categories are now in
    the schema as an enum. The enum stops the agent from SENDING a bad category;
    this tool is how it TELLS THE USER what the real options are.
    """
    return ", ".join(CATEGORIES)


ALL_TOOLS: list[Tool] = [
    get_today,
    log_expense,
    month_total,
    get_budget,
    subtract,
    list_recent,
    list_categories,
]
