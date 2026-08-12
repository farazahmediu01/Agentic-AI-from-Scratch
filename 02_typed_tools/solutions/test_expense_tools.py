"""
The adversarial dataset — Spendly Lite v2's boundary, under attack.

    uv run pytest 02_typed_tools/solutions/ -v

Read this before you read the tests.

This file is the first real test suite in the curriculum, and it is deliberately
the cheapest kind: **no API key, no network, no model, no cost, sub-second.**
That is possible because of what Chapter 2 built. The tool boundary is a pure
function of a JSON string, so it can be attacked directly, thousands of times,
without an agent anywhere near it.

That property is worth more than the tests themselves. Every eval you write in
Chapter 5 will cost a real model call and take minutes; this costs nothing and
takes milliseconds. So the rule is: **push every assertion you can down to the
boundary, and spend model calls only on what genuinely needs a model.**

  Needs a model : did the agent decide to ask instead of guess?
  Does NOT      : is a negative amount rejected? is 'astrology' rejected?

Chapter 1 could not have this file. Its validation lived inside function bodies
that touched storage, so testing "is a bad category rejected" meant writing to
a JSON file and cleaning up afterwards. Moving the checks to the boundary made
them testable in isolation. That is not a side effect — it is the main
structural benefit of the chapter, and this file is the proof.

Every case below is a payload a model could plausibly emit. Add to it whenever
you catch a new one in the wild; that is how a golden dataset grows.
"""

from __future__ import annotations

import json

import pytest

import expense_store
from chapter import ToolError
from expense_store import CATEGORIES
from expense_tools import ALL_TOOLS, list_categories, log_expense, month_total

TOOLS_BY_NAME = {t.name: t for t in ALL_TOOLS}


# -----------------------------------------------------------------------------
# Fixture: every test starts from the same known ledger and leaves nothing
# behind. A test that depends on the previous test's leftovers is not a test.
# -----------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def clean_store():
    expense_store.reset(seeded=True)
    yield
    expense_store.reset(seeded=True)


def logged_rows() -> list[expense_store.Expense]:
    """Expenses written during this test (seeds are tagged and excluded)."""
    return [r for r in expense_store.all_expenses() if r["notes"] != "seed"]


# -----------------------------------------------------------------------------
# 1. The attacks. Each one must be REJECTED, and must write nothing.
# -----------------------------------------------------------------------------

ATTACKS: list[tuple[str, str, str, str]] = [
    (
        "negative amount",
        "log_expense",
        '{"vendor": "Imtiaz", "amount": -450, "category": "Groceries"}',
        "amount",
    ),
    (
        "zero amount",
        "log_expense",
        '{"vendor": "Imtiaz", "amount": 0, "category": "Groceries"}',
        "amount",
    ),
    (
        "amount as a word",
        "log_expense",
        '{"vendor": "KFC", "amount": "fifteen hundred", "category": "Food & Dining"}',
        "amount",
    ),
    (
        "amount as a boolean",
        "log_expense",
        '{"vendor": "KFC", "amount": true, "category": "Food & Dining"}',
        "amount",
    ),
    (
        "invented category",
        "log_expense",
        '{"vendor": "Al-Falah", "amount": 2000, "category": "astrology"}',
        "category",
    ),
    (
        "category with wrong casing",
        "log_expense",
        '{"vendor": "KFC", "amount": 1500, "category": "food & dining"}',
        "category",
    ),
    (
        "blank vendor",
        "log_expense",
        '{"vendor": "   ", "amount": 1500, "category": "Food & Dining"}',
        "vendor",
    ),
    (
        "missing amount",
        "log_expense",
        '{"vendor": "KFC", "category": "Food & Dining"}',
        "amount",
    ),
    (
        "invented parameter",
        "log_expense",
        '{"vendor": "KFC", "amount": 1500, "category": "Food & Dining", "tip": 200}',
        "tip",
    ),
    (
        "date in the wrong format",
        "log_expense",
        '{"vendor": "KFC", "amount": 1500, "category": "Food & Dining", "expense_date": "13/08/2026"}',
        "expense_date",
    ),
    (
        "date in the future",
        "log_expense",
        '{"vendor": "KFC", "amount": 1500, "category": "Food & Dining", "expense_date": "2099-01-01"}',
        "future",
    ),
    (
        "truncated JSON",
        "log_expense",
        '{"vendor": "KFC", "amount":',
        "JSON",
    ),
    (
        "arguments sent as a list",
        "log_expense",
        '["KFC", 1500, "Food & Dining"]',
        "object",
    ),
    (
        "month in the wrong format",
        "month_total",
        '{"category": "Food & Dining", "month": "August 2026"}',
        "month",
    ),
    (
        "limit out of range",
        "list_recent",
        '{"limit": 5000}',
        "limit",
    ),
    (
        "argument passed to a tool that takes none",
        "list_categories",
        '{"verbose": true}',
        "verbose",
    ),
]


@pytest.mark.parametrize(
    ("label", "tool_name", "raw", "must_mention"),
    ATTACKS,
    ids=[a[0] for a in ATTACKS],
)
def test_attack_is_rejected(label: str, tool_name: str, raw: str, must_mention: str) -> None:
    """Every hostile payload is rejected, and the rejection says what went wrong."""
    with pytest.raises(ToolError) as caught:
        TOOLS_BY_NAME[tool_name].call(raw)

    message = str(caught.value)
    assert must_mention.lower() in message.lower(), (
        f"{label}: the error must name '{must_mention}' or the model cannot fix it.\nGot: {message}"
    )


@pytest.mark.parametrize(
    ("label", "tool_name", "raw", "must_mention"),
    ATTACKS,
    ids=[a[0] for a in ATTACKS],
)
def test_attack_writes_nothing(label: str, tool_name: str, raw: str, must_mention: str) -> None:
    """
    The property that actually matters.

    A rejected call must have NO side effects. This is separate from the test
    above on purpose: an error message is a nicety, an untouched ledger is the
    guarantee. If validation ever moves back inside the function body, the test
    above keeps passing and this one starts failing.
    """
    with pytest.raises(ToolError):
        TOOLS_BY_NAME[tool_name].call(raw)

    assert logged_rows() == [], f"{label}: a rejected call wrote to the ledger"


# -----------------------------------------------------------------------------
# 2. The happy paths. A boundary that rejects everything is not a boundary,
#    it is a wall. Validation is only correct if valid calls still get through.
# -----------------------------------------------------------------------------


def test_valid_call_writes_exactly_one_row() -> None:
    result = log_expense.call('{"vendor": "KFC", "amount": 1500, "category": "Food & Dining"}')
    rows = logged_rows()
    assert len(rows) == 1
    assert rows[0]["amount"] == 1500.0
    assert rows[0]["category"] == "Food & Dining"
    assert "Logged" in result


def test_numeric_string_is_coerced_not_rejected() -> None:
    """
    `"1500"` becomes 1500.0, and that is the correct behaviour.

    Look back at `from_scratch/break_it.py`, where `add(a="5", b="3")` returned
    "53". The fix was never "reject strings" — models quote numbers constantly
    and rejecting every one would burn turns on a problem with a right answer.
    The fix is to COERCE at the boundary so the function body receives a float.

    That is the difference between validating and parsing. A validator answers
    yes or no. A parser returns the value in the shape the rest of your code
    was written for, and Pydantic is a parser.
    """
    log_expense.call('{"vendor": "KFC", "amount": "1500", "category": "Food & Dining"}')
    rows = logged_rows()
    assert rows[0]["amount"] == 1500.0
    assert isinstance(rows[0]["amount"], float)


def test_vendor_whitespace_is_stripped() -> None:
    log_expense.call('{"vendor": "  KFC  ", "amount": 1500, "category": "Food & Dining"}')
    assert logged_rows()[0]["vendor"] == "KFC"


def test_omitted_optional_date_defaults_to_today() -> None:
    from datetime import date

    log_expense.call('{"vendor": "KFC", "amount": 1500, "category": "Food & Dining"}')
    assert logged_rows()[0]["date"] == date.today().isoformat()


def test_empty_string_date_is_accepted() -> None:
    """The wrinkle from `expense_tools.py`: the default value must pass its own pattern."""
    log_expense.call(
        '{"vendor": "KFC", "amount": 1500, "category": "Food & Dining", "expense_date": ""}'
    )
    assert len(logged_rows()) == 1


def test_read_only_tool_writes_nothing() -> None:
    month_total.call('{"category": "Food & Dining"}')
    assert logged_rows() == []


# -----------------------------------------------------------------------------
# 3. The contract itself. These test the SCHEMA, not the behaviour — they catch
#    the failure mode where the code is right and the model was never told.
# -----------------------------------------------------------------------------


def test_every_tool_has_a_description() -> None:
    for tool in ALL_TOOLS:
        assert tool.description.strip(), f"{tool.name} would be invisible to the model"


def test_category_enum_reaches_the_schema() -> None:
    """
    The whole Chapter 2 thesis in one assertion.

    Chapter 1 described the ten categories in an English sentence and hoped.
    If this assertion ever fails, the model is guessing again.
    """
    enum = log_expense.parameters["properties"]["category"]["enum"]
    assert set(enum) == set(CATEGORIES)


def test_amount_constraint_reaches_the_schema() -> None:
    assert log_expense.parameters["properties"]["amount"]["exclusiveMinimum"] == 0


def test_schemas_forbid_unknown_arguments() -> None:
    for tool in ALL_TOOLS:
        assert tool.parameters.get("additionalProperties") is False, (
            f"{tool.name} would silently ignore invented arguments"
        )


def test_no_pydantic_constraint_names_leak_into_the_schema() -> None:
    """
    Guards a bug this suite actually caught.

    Pydantic normally translates `gt=0` into JSON Schema's `exclusiveMinimum`.
    Add a custom validator to the same field and it stops being able to, and
    emits the raw `"gt": 0` instead -- which is not a JSON Schema keyword, so
    the model never learns the constraint exists. Nothing crashes; you just
    quietly pay for a round trip you thought you had designed out.

    `_clean_schema` in `typed_tool.py` renames them. This test is why it exists.
    """
    leaky = {"gt", "ge", "lt", "le", "multiple_of", "min_length", "max_length"}
    for tool in ALL_TOOLS:
        for field_name, prop in tool.parameters.get("properties", {}).items():
            found = leaky & set(prop)
            assert not found, f"{tool.name}.{field_name} leaks Pydantic constraint names: {found}"


def test_schemas_are_json_serialisable() -> None:
    """
    Cheap, and it has caught real bugs.

    Everything in a schema is sent over the wire. A default value that is a
    `date` or a `Decimal` type-checks perfectly and fails at request time.
    """
    for tool in ALL_TOOLS:
        json.dumps(tool.schema)


def test_no_two_tools_share_a_name() -> None:
    names = [t.name for t in ALL_TOOLS]
    assert len(names) == len(set(names))


def test_list_categories_matches_the_enum() -> None:
    """
    The tool that TELLS the user the options must agree with the enum that
    CONSTRAINS the model. Two lists, one truth — assert it, do not assume it.
    """
    spoken = {c.strip() for c in list_categories.call("{}").split(",")}
    assert spoken == set(CATEGORIES)
