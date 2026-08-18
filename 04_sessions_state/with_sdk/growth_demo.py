"""
OBSERVE: what a session costs.

    uv run python 04_sessions_state/with_sdk/growth_demo.py

Chapter 4 gives your agent a memory in one keyword argument. This file is the
invoice.

A session only ever appends. Nothing in `SQLiteSession` prunes, summarises,
forgets or expires -- and because Chat Completions is stateless, every stored
item is re-uploaded on every subsequent turn. Turn 10 does not send turn 10. It
sends turns 1 through 10.

    PART 1   measure it     -- history size and tokens, per turn
    PART 2   two objects    -- the same session_id is not the same conversation
    PART 3   the one knob   -- SessionSettings(limit=N), and why it is a chainsaw

PARTS 2 AND 3 COST NO API CALLS. They only re-read what PART 1 stored.

WHY THE NUMBERS BELOW ARE SMALLER THAN YOU EXPECT
--------------------------------------------------
The first version of this file printed a turn-over-turn ratio and the ratio was
about 1.1x, which made the chapter's argument look weak. The ratio was not
wrong; the metric was. Two corrections, both worth knowing before you measure
token growth in your own agent:

  * A run's `usage.input_tokens` is the SUM over every request that run made.
    A turn with two tool calls is three requests, so it out-totals a longer turn
    that only needed one. Divide by `usage.requests` or you are measuring tool
    chattiness, not history.
  * At turn 5 the FIXED cost dominates: system prompt plus four tool schemas is
    roughly a thousand tokens before the conversation says anything. Growth is
    perfectly real and perfectly invisible underneath it.

That second point is the honest version of this chapter's warning. The bill does
not arrive as a cliff you can see coming. It arrives as a slope you cannot see
at all until the fixed cost stops being the biggest number -- which is exactly
why "we'll add trimming when it becomes a problem" is a plan that fails.
"""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from agents import Runner, SQLiteSession
from agents.memory.session_settings import SessionSettings

from packing_agent import Traveller, agent

PACE_SECONDS = 10.0

# File-backed on purpose. An in-memory session lives inside the Python object,
# so PART 2 could not exist against ':memory:' -- see PART 2 for what that
# actually looks like when you get it wrong.
DB_PATH = Path(__file__).parent / "data" / "growth_demo.db"
SESSION_ID = "growth_demo"

TURNS = [
    "Pack two t-shirts, 0.2 kg each.",
    "Add a pair of jeans, 0.8 kg.",
    "Add a jacket, 1.2 kg.",
    "Add hiking boots, 1.5 kg.",
    "How much room do I have left?",
]


def kind_of(item: Any) -> str:
    """One label per stored item. `TResponseInputItem` is a union of TypedDicts."""
    return str(item.get("role") or item.get("type") or "?")


def history_bytes(items: list[Any]) -> int:
    """
    How big the stored transcript is, in characters of JSON.

    Deterministic, free, and monotonic -- which is what makes it the right thing
    to graph. Tokens wobble with tool chattiness; the transcript only grows.
    """
    return len(json.dumps(items))


async def part_1_measure(session: SQLiteSession) -> None:
    print("=" * 78)
    print("PART 1 - MEASURED. Five turns, one session.")
    print("=" * 78)
    print(f"  {'turn':<6}{'items':>7}{'history':>10}{'reqs':>7}{'in tok':>9}{'tok/req':>9}   agent")
    print("  " + "-" * 76)

    traveller = Traveller(name="Faraz", bag_limit_kg=20.0)

    for number, prompt in enumerate(TURNS, start=1):
        result = await Runner.run(agent, prompt, context=traveller, session=session)
        items = await session.get_items()
        usage = result.context_wrapper.usage
        per_request = usage.input_tokens / max(usage.requests, 1)
        answer = str(result.final_output)
        answer = answer if len(answer) <= 28 else answer[:25] + "..."
        print(
            f"  {number:<6}{len(items):>7}{history_bytes(items):>10,}"
            f"{usage.requests:>7}{usage.input_tokens:>9,}{per_request:>9,.0f}   {answer}"
        )
        await asyncio.sleep(PACE_SECONDS)

    print(
        "\n  Two columns matter. `history` only ever goes up -- that is the claim of\n"
        "  this section, and it is not a tendency, it is arithmetic. `tok/req` is\n"
        "  what you are billed for reading, per request, and it climbs with it.\n"
        "\n  Now extrapolate rather than trusting turn 5. A steady ~130 tokens per\n"
        "  turn of history is nothing at turn 5 and is the whole request at turn\n"
        "  200. Nobody notices in a demo. Everybody notices in production, usually\n"
        "  as a bill, sometimes as a hard context-length error mid-conversation."
    )


async def part_2_same_id_is_not_the_same_conversation() -> None:
    """Free. This is a trap this file fell into while it was being written."""
    print("\n" + "=" * 78)
    print("PART 2 - A session_id IS NOT A SESSION. Where the items actually live.")
    print("=" * 78)

    same_db = SQLiteSession(SESSION_ID, DB_PATH)
    in_memory = SQLiteSession(SESSION_ID)  # same id, DIFFERENT database

    print(f"  SQLiteSession('{SESSION_ID}', DB_PATH)  -> {len(await same_db.get_items()):>3} items")
    print(
        f"  SQLiteSession('{SESSION_ID}')           -> {len(await in_memory.get_items()):>3} items"
    )
    print(
        "\n  Identical session_id. One has the conversation, one is empty, and no\n"
        "  error was raised by either. The id names a ROW; the db_path names the\n"
        "  BOOK it is a row in, and `db_path` defaults to ':memory:' -- a database\n"
        "  that lives inside that one Python object and dies with it.\n"
        "\n  This is the shape of the bug: it works all through development, because\n"
        "  a dev server is one process holding one object. It fails the moment you\n"
        "  run two workers, restart on deploy, or scale to two pods -- and it fails\n"
        "  as 'the agent forgot everything', which reads like a model problem."
    )


async def part_3_the_one_knob() -> None:
    """Free."""
    print("\n" + "=" * 78)
    print("PART 3 - THE ONE KNOB THE SDK GIVES YOU, AND ITS SHARP EDGE")
    print("=" * 78)

    session = SQLiteSession(SESSION_ID, DB_PATH)
    everything = await session.get_items()
    print(f"  full history: {len(everything)} items, {history_bytes(everything):,} chars")
    print(f"\n  {'limit':<8}{'items':>7}{'chars':>9}   {'first item':<22}orphaned?")
    print("  " + "-" * 62)

    for limit in (2, 3, 4, 6, 8):
        window = await session.get_items(limit=limit)
        first = kind_of(window[0]) if window else "-"
        # An orphan is a tool RESULT whose CALL fell outside the window. The model
        # is handed an answer to a question it cannot see having asked.
        orphan = first in {"function_call_output", "tool"}
        print(
            f"  {limit:<8}{len(window):>7}{history_bytes(window):>9,}   "
            f"{first:<22}{'YES' if orphan else 'no'}"
        )

    capped = SQLiteSession(SESSION_ID, DB_PATH, session_settings=SessionSettings(limit=6))
    print(f"\n  SessionSettings(limit=6) on the session: {len(await capped.get_items())} items")
    print("  (the same cap, declared once, instead of passed at every read)")

    print(
        "\n  WHAT THIS KNOB ACTUALLY IS. `limit` takes the LAST N items. It is a\n"
        "  tail window -- not a summariser, not a compactor:\n"
        "\n    - the database still grows forever. `limit` changes what you READ,\n"
        "      never what you STORE.\n"
        "    - it counts ITEMS, not tokens. One item can be four tokens or four\n"
        "      thousand, so it caps the wrong unit for the problem it solves.\n"
        "    - see the orphaned? column. A window can start on a tool RESULT whose\n"
        "      CALL was cut away. Some providers reject that outright.\n"
        "    - the oldest turn is usually where the user said what they WANT. A\n"
        "      tail window throws away precisely the wrong end.\n"
        "\n  So the SDK hands you a chainsaw and correctly declines to decide how to\n"
        "  swing it. Deciding -- trimming on tokens, keeping call/result pairs\n"
        "  together, summarising the head instead of dropping it -- is Chapter 5."
    )


async def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    session = SQLiteSession(SESSION_ID, DB_PATH)
    # Determinism: this demo prints counts, so it must not inherit yesterday's run.
    await session.clear_session()

    await part_1_measure(session)
    await part_2_same_id_is_not_the_same_conversation()
    await part_3_the_one_knob()


if __name__ == "__main__":
    asyncio.run(main())
