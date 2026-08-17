"""
Boundary tests for the OUTPUT contract. No API key, no network, ~0.1 seconds.

Chapter 2 established the rule and this file applies it in the new direction:

    Is a bad shape rejected? Does the enum reach the schema?  -> pytest, free
    Did the agent choose the right branch?                    -> check_expenses.py

Every test below asks a question about `replies.py` as a pure function of a dict.
None of them needs a model, because none of them is about the model -- they are
about whether the contract we published is the contract we meant.

That distinction is the one students get wrong most often. "Test the agent" is
expensive, slow and flaky. "Test the shape the agent must fit into" is free,
instant and deterministic -- and it catches a large fraction of the bugs that
would otherwise show up as mysterious eval failures six minutes into a run.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

import _bootstrap  # noqa: F401  -- must precede every spine import
from expense_store import CATEGORIES
from replies import Logged, NeedMoreInfo, Refused, Reported, SpendlyReply

# -----------------------------------------------------------------------------
# The exactly-one-branch rule. This is the check the schema cannot express, so
# it is the one most worth testing.
# -----------------------------------------------------------------------------

LOGGED = {
    "reply": "Logged PKR 1500 at KFC.",
    "vendor": "KFC",
    "amount": 1500,
    "category": "Food & Dining",
}
ASKING = {"question": "How much did you spend?", "missing": ["amount"]}


def test_exactly_one_branch_is_accepted() -> None:
    reply = SpendlyReply.model_validate({"logged": LOGGED})
    assert reply.branch == "logged"


def test_zero_branches_is_rejected() -> None:
    """
    The failure mode nobody expects. `output_type=` guarantees a SpendlyReply;
    it does not guarantee the SpendlyReply says anything. All four fields are
    optional, so `{}` satisfies the schema perfectly and means nothing.
    """
    with pytest.raises(ValidationError, match="exactly one branch"):
        SpendlyReply.model_validate({})


def test_two_branches_is_rejected() -> None:
    """A model that both logged and asked has contradicted itself."""
    with pytest.raises(ValidationError, match="exactly one branch"):
        SpendlyReply.model_validate({"logged": LOGGED, "need_more_info": ASKING})


def test_branch_property_names_the_set_field() -> None:
    assert SpendlyReply.model_validate({"need_more_info": ASKING}).branch == "need_more_info"
    assert (
        SpendlyReply.model_validate(
            {"refused": {"reply": "no", "reason": "future_date", "offending_value": "2099-01-01"}}
        ).branch
        == "refused"
    )


# -----------------------------------------------------------------------------
# Constraints on the branches themselves.
# -----------------------------------------------------------------------------


def test_logged_rejects_a_non_positive_amount() -> None:
    """
    `gt=0` on the way OUT, mirroring Chapter 2's `gt=0` on the way IN.

    Worth pausing on: the tool already refuses to write a negative amount, so
    why constrain the report of it? Because the tool and the sentence are two
    different claims. An agent can log 1500 correctly and then tell the user it
    logged -1500. Chapter 2 guarded the write; this guards the telling.
    """
    with pytest.raises(ValidationError):
        Logged.model_validate({**LOGGED, "amount": -1})
    with pytest.raises(ValidationError):
        Logged.model_validate({**LOGGED, "amount": 0})


def test_logged_category_is_the_closed_set() -> None:
    """The same `Category` type from Chapter 2, now constraining an output."""
    with pytest.raises(ValidationError):
        Logged.model_validate({**LOGGED, "category": "Astrology"})


def test_category_enum_reaches_the_output_schema() -> None:
    """
    The Chapter 2 lesson, applied to outputs: a model can behave perfectly and
    still be broken if the contract it published was wrong. This asserts on the
    SCHEMA, not the behaviour.
    """
    schema = SpendlyReply.model_json_schema()
    enum = schema["$defs"]["Logged"]["properties"]["category"]["enum"]
    assert set(enum) == set(CATEGORIES)


def test_refusal_reason_is_a_closed_set() -> None:
    """
    If `reason` were a free-text string, `check_expenses.py` case 5 would be back
    to substring matching -- which is exactly what this chapter deletes.
    """
    with pytest.raises(ValidationError):
        Refused.model_validate(
            {"reply": "no", "reason": "the amount was a bit odd", "offending_value": "-450"}
        )


def test_missing_fields_are_a_closed_set() -> None:
    """`missing: ['amt']` would pass a plain `list[str]` and break every eval."""
    with pytest.raises(ValidationError):
        NeedMoreInfo.model_validate({"question": "?", "missing": ["amt"]})


def test_reported_allows_all_figures_to_be_absent() -> None:
    """
    Not every question is about a number. "What categories exist?" is a
    `Reported` with nothing but a sentence, and forcing a `spent` figure there
    is precisely how you teach a model to invent one.
    """
    reported = Reported.model_validate({"reply": "You have ten categories."})
    assert reported.spent is None


# -----------------------------------------------------------------------------
# The honest limit — see README section 8.
# -----------------------------------------------------------------------------


def test_a_valid_shape_can_still_be_a_lie() -> None:
    """
    This test PASSES, and that is the uncomfortable point.

    Every constraint is satisfied. The amount is positive, the category is real,
    the branch is singular. The numbers are also completely fabricated: nothing
    was written to any ledger and no budget was consulted.

    A schema guarantees SHAPE. It does not guarantee TRUTH. Chapter 2 learned
    that a type stops a bad value but not an invented one; this is the same
    lesson one level up, and the fix is in the same place -- a check that runs
    outside the model, comparing what it said against what actually happened.
    """
    reply = SpendlyReply.model_validate(
        {
            "logged": {
                "reply": "Logged PKR 999999 at Definitely Real Vendor.",
                "vendor": "Definitely Real Vendor",
                "amount": 999999,
                "category": "Groceries",
                "remaining": 123456,
            }
        }
    )
    assert reply.branch == "logged"
    assert reply.logged is not None
    assert reply.logged.amount == 999999
