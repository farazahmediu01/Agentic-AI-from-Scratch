"""
Spendly Lite v4 — the context object.

    A session is what the agent REMEMBERS.
    A context is what you HAND it.

This file is the second half of that sentence. It holds nothing the model will
ever read: `User` is a plain Python object that travels alongside the run, is
handed to tool bodies, and is never serialised into a message. Prove that to
yourself in `../with_sdk/context_demo.py` before you trust the claim.

WHY BUDGETS, AND NOT SOMETHING EASIER
-------------------------------------
A context object carrying something incidental -- a request id, a feature flag,
a logger -- makes dependency injection look decorative, and a student who thinks
a primitive is decorative will not reach for it when they need it.

So Chapter 4 moves a rule that was previously a LAW into the context: the
monthly budget. Through Chapters 1-3, `MONTHLY_BUDGETS` was a module-level dict,
which quietly asserted that every user of Spendly has the same budget. That was
never true of any real expense product; it was true only because there was one
user and they were hard-coded.

    Chapters 1-3   get_budget(category)             -> MONTHLY_BUDGETS[category]
    Chapter 4      get_budget(ctx, category)        -> ctx.context.budget_for(category)

The observable consequence, and the reason this is worth a chapter section:
**the same agent, the same prompt, and the same ledger now produce two different
correct answers.** Case M5 in `check_multiturn.py` asserts exactly that.

WHAT DID *NOT* MOVE, AND WHY THAT IS THE INTERESTING HALF
----------------------------------------------------------
The ledger did not move. Expenses still live in `expense_store`, shared.

That is deliberate, and it is the distinction students most often blur:

    a CONTEXT holds what your app knows about THIS RUN     (who is asking)
    a STORE   holds what your app knows, period            (what happened)

A budget is configuration attached to a person. An expense is a fact about the
world. Put facts in a context and you will find yourself passing your database
around as an argument; put configuration in a store and you will find yourself
adding a `user_id` column to a settings table. Making Spendly's ledger genuinely
per-user is Challenge 2 in `../EXERCISES.md` -- it is a real change, and the
point of leaving it undone is that you can see where the seam would go.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import _bootstrap  # noqa: F401  -- must precede every spine import; see _bootstrap.py
from expense_store import CATEGORIES, MONTHLY_BUDGETS

__all__ = ["AYESHA", "FARAZ", "USERS", "User", "default_user"]


@dataclass
class User:
    """
    Everything a run needs to know about who is asking.

    Note what is NOT here: no API key, no database handle, no model client. Not
    because the type would object -- it would not -- but because this object is
    handed to every tool body, and the smallest object that answers "who is
    asking" is the one that stays comprehensible at Chapter 10.
    """

    user_id: str
    name: str
    timezone: str = "Asia/Karachi"
    monthly_income: float = 0.0

    # `default_factory` and not `= MONTHLY_BUDGETS`, for two separate reasons and
    # both of them are bugs waiting to happen:
    #
    #   1. A mutable default is shared by every instance that takes it. Two users
    #      would hold the SAME dict, and raising one person's food budget would
    #      raise everybody's. ruff's B006 catches the literal form of this
    #      (`budgets: dict = {}`); it does not catch handing over a module-level
    #      dict, which is the same bug with better manners.
    #   2. `dict(...)` copies. Without the copy, `default_factory=lambda:
    #      MONTHLY_BUDGETS` would still hand out one shared object.
    budgets: dict[str, float] = field(default_factory=lambda: dict(MONTHLY_BUDGETS))

    def budget_for(self, category: str) -> float:
        """
        This user's monthly budget for one category.

        The error message is not politeness. When budgets were module-level, a
        missing category was impossible -- one dict, checked once, forever. Per
        user, every user's dict is a chance to miss one, and the failure arrives
        as a bare `KeyError: 'Groceries'` from inside a tool the model called.
        `test_context.py` turns that into a test instead.
        """
        try:
            return self.budgets[category]
        except KeyError:
            raise KeyError(
                f"{self.name} has no budget set for {category!r}. "
                f"Known categories: {', '.join(sorted(self.budgets))}"
            ) from None


# -----------------------------------------------------------------------------
# Two users, chosen so that the SAME question has two different right answers.
#
# The seeded ledger holds 7500 of Food & Dining spending this month (see
# `expense_store.SEEDED_FOOD_TOTAL`). So:
#
#     "How much of my food budget is left?"   Faraz  -> 25000 - 7500 = 17500
#                                             Ayesha ->  9000 - 7500 =  1500
#
# Same agent. Same prompt. Same ledger. Same tools. One argument different.
# -----------------------------------------------------------------------------

FARAZ = User(
    user_id="u_faraz",
    name="Faraz",
    timezone="Asia/Karachi",
    monthly_income=350_000.0,
    # No `budgets=` -- takes a copy of Chapter 2's table, so every figure
    # Chapters 1-3 asserted on is still the figure this user gets. That is not a
    # coincidence; it is how Chapter 3's dataset keeps passing against v4.
)

AYESHA = User(
    user_id="u_ayesha",
    name="Ayesha",
    timezone="Asia/Karachi",
    monthly_income=40_000.0,
    # A student's budget. Written out in full rather than scaled from Faraz's,
    # because a real per-user budget is not a multiplier -- Education goes UP
    # relative to income, Shopping goes down. Configuration that can be computed
    # from other configuration was never configuration.
    budgets={
        "Food & Dining": 9_000.0,
        "Transportation": 4_000.0,
        "Shopping": 3_000.0,
        "Bills & Utilities": 5_000.0,
        "Entertainment": 2_500.0,
        "Health & Medical": 3_000.0,
        "Education": 12_000.0,
        "Groceries": 8_000.0,
        "Office Supplies": 1_500.0,
        "Miscellaneous": 2_000.0,
    },
)

USERS: dict[str, User] = {u.user_id: u for u in (FARAZ, AYESHA)}


def default_user() -> User:
    """
    The user every Chapter 1-3 assertion was implicitly written against.

    `check_regression.py` runs Chapter 3's nine cases through v4 with this user,
    which is what makes "the regression rule" a command you can run rather than
    a hope.
    """
    return FARAZ


# A cheap invariant, asserted at import rather than discovered at runtime. If a
# category is ever added to `expense_store.Category`, every user's budget dict
# must gain it -- and the failure should arrive here, at startup, not three
# turns into a conversation.
for _user in USERS.values():
    _missing = [c for c in CATEGORIES if c not in _user.budgets]
    if _missing:  # pragma: no cover -- guarded by test_context.py
        raise ValueError(f"{_user.name} is missing budgets for: {_missing}")
