"""
Offline tests for Chapter 4. No API key, no network, ~1 second.

    uv run pytest 04_sessions_state -q

Chapter 2 bought 46 tests by putting a contract on the tool boundary. Chapter 3
bought 11 by putting one on the output. Chapter 4's new surface is state, and
state is the cheapest thing in this whole curriculum to test -- a session is a
table and a context is a dataclass, and neither needs a model to be wrong.

That is worth saying plainly, because "we can't test the agent" is the sentence
that ends most people's testing story. You are not testing the agent here. You
are testing everything around it, which is where most of your bugs will be.

Note the async style: `asyncio.run(...)` inside an ordinary sync test, exactly
as Chapter 0 section 5 showed. No pytest-asyncio, no plugin, no marker. The SDK's
session API is async; pytest does not have to be.
"""

from __future__ import annotations

import asyncio
from typing import Any

import pytest
from agents import SQLiteSession

import _bootstrap  # noqa: F401  -- must precede every spine import
from expense_store import CATEGORIES, MONTHLY_BUDGETS
from spendly_context import AYESHA, FARAZ, USERS, User, default_user

# -----------------------------------------------------------------------------
# The context object
# -----------------------------------------------------------------------------


def test_every_user_has_a_budget_for_every_category() -> None:
    """
    The invariant that per-user budgets create and module-level budgets could not.

    One dict checked once is safe forever. Ten dicts are ten chances to miss a
    category, and the miss surfaces as a bare KeyError from inside a tool call
    three turns into a conversation. Better here.
    """
    for user in USERS.values():
        missing = [c for c in CATEGORIES if c not in user.budgets]
        assert not missing, f"{user.name} has no budget for {missing}"


def test_two_users_do_not_share_a_budget_dict() -> None:
    """
    The mutable-default bug, asserted rather than hoped for.

    `budgets: dict[str, float] = MONTHLY_BUDGETS` would pass every test that
    only reads. It fails the moment anything writes -- and then it fails for
    every user at once, silently, in a way that looks like a data problem.
    """
    a = User(user_id="u_a", name="A")
    b = User(user_id="u_b", name="B")
    assert a.budgets is not b.budgets

    a.budgets["Food & Dining"] = 1.0
    assert b.budgets["Food & Dining"] != 1.0
    assert MONTHLY_BUDGETS["Food & Dining"] != 1.0, "the module-level table was mutated"


def test_the_default_user_matches_chapters_1_to_3() -> None:
    """
    Why `check_regression.py` can pass at all.

    Chapters 1-3 asserted on figures like `25000 - 7500 = 17500`. Those numbers
    came from `MONTHLY_BUDGETS`. If the default user drifted from that table,
    every earlier chapter's dataset would fail for a reason having nothing to do
    with the chapter it was testing.
    """
    assert default_user() is FARAZ
    assert FARAZ.budgets == MONTHLY_BUDGETS


def test_the_two_users_disagree_about_food() -> None:
    """The premise of golden-dataset case M5. If this is ever equal, M5 proves nothing."""
    assert FARAZ.budget_for("Food & Dining") != AYESHA.budget_for("Food & Dining")


def test_an_unknown_category_names_the_user_and_the_options() -> None:
    with pytest.raises(KeyError) as caught:
        FARAZ.budget_for("Yacht Maintenance")
    message = str(caught.value)
    assert "Faraz" in message
    assert "Food & Dining" in message


def test_users_are_registered_under_their_own_id() -> None:
    for key, user in USERS.items():
        assert key == user.user_id


# -----------------------------------------------------------------------------
# The session
#
# Every test below drives `SQLiteSession` directly, with no agent and no model.
# A session is storage; storage is testable.
# -----------------------------------------------------------------------------


def items(*roles: str) -> list[Any]:
    return [{"role": role, "content": f"message from {role}"} for role in roles]


def test_a_session_round_trips_what_you_put_in_it() -> None:
    async def go() -> list[Any]:
        session = SQLiteSession("t_round_trip")
        await session.add_items(items("user", "assistant"))
        return await session.get_items()

    stored = asyncio.run(go())
    assert len(stored) == 2
    assert stored[0]["role"] == "user"


def test_two_sessions_with_the_same_id_can_be_different_conversations() -> None:
    """
    The trap `growth_demo.py` PART 2 demonstrates, pinned as a test.

    `db_path` defaults to ':memory:', which is a database living inside ONE
    Python object. Same id, two objects, two universes -- and no error. This
    test exists so the behaviour is documented rather than rediscovered at 2am
    when a second worker process starts answering the same user.
    """

    async def go() -> tuple[int, int]:
        first = SQLiteSession("t_same_id")
        second = SQLiteSession("t_same_id")
        await first.add_items(items("user"))
        return len(await first.get_items()), len(await second.get_items())

    assert asyncio.run(go()) == (1, 0)


def test_a_session_only_grows() -> None:
    """Section 9's claim, as arithmetic rather than as a warning."""

    async def go() -> list[int]:
        session = SQLiteSession("t_growth")
        counts: list[int] = []
        for _ in range(5):
            await session.add_items(items("user", "assistant"))
            counts.append(len(await session.get_items()))
        return counts

    counts = asyncio.run(go())
    assert counts == [2, 4, 6, 8, 10]
    assert counts == sorted(counts), "a session never shrinks on its own"


def test_limit_is_a_tail_window_not_a_summary() -> None:
    """
    `limit=N` returns the LAST N items. Not the most relevant N, not a summary.

    Asserting which END it keeps is the point: the oldest turn is usually where
    the user said what they actually want, and a tail window is exactly the
    wrong end to discard. That is Chapter 5's opening argument.
    """

    async def go() -> list[Any]:
        session = SQLiteSession("t_limit")
        await session.add_items([{"role": "user", "content": str(n)} for n in range(10)])
        return await session.get_items(limit=3)

    window = asyncio.run(go())
    assert [item["content"] for item in window] == ["7", "8", "9"]


def test_a_limit_can_orphan_a_tool_call_from_its_result() -> None:
    """
    The sharp edge on the only knob the SDK gives you.

    A window that starts on a `function_call_output` hands the model the answer
    to a question it cannot see having asked. Some providers reject the request
    outright; the ones that do not are arguably worse, because the model now
    reasons over a result it has no idea how it obtained.
    """

    async def go() -> list[Any]:
        session = SQLiteSession("t_orphan")
        await session.add_items(
            [
                {"role": "user", "content": "what is the total?"},
                {"type": "function_call", "call_id": "c1", "name": "total", "arguments": "{}"},
                {"type": "function_call_output", "call_id": "c1", "output": "9000"},
            ]
        )
        return await session.get_items(limit=1)

    window = asyncio.run(go())
    assert window[0]["type"] == "function_call_output"
    assert not any(item.get("type") == "function_call" for item in window)


def test_clearing_a_session_empties_it_without_deleting_the_database() -> None:
    """`clear_session()` is the reset every deterministic harness needs."""

    async def go() -> tuple[int, int]:
        session = SQLiteSession("t_clear")
        await session.add_items(items("user", "assistant"))
        before = len(await session.get_items())
        await session.clear_session()
        return before, len(await session.get_items())

    assert asyncio.run(go()) == (2, 0)


def test_pop_item_removes_the_newest_item() -> None:
    """
    The repair tool for a retry that half-happened.

    `Runner.run` writes the user's message into the session as it starts, so a
    run that dies mid-flight can leave it behind -- and a naive retry then says
    the same thing twice. `pop_item()` is how a product fixes that. See the
    docstring on `_run_with_backoff` in `expense_agent_v4.py` for why the test
    HARNESS deliberately does not.
    """

    async def go() -> tuple[Any, list[Any]]:
        session = SQLiteSession("t_pop")
        await session.add_items(items("user", "assistant"))
        popped = await session.pop_item()
        return popped, await session.get_items()

    popped, remaining = asyncio.run(go())
    assert popped is not None and popped["role"] == "assistant"
    assert len(remaining) == 1
