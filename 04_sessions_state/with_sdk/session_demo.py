"""
OBSERVE: what a session actually holds.

    uv run python 04_sessions_state/with_sdk/session_demo.py

This is the chapter's one Observe block, and it exists instead of a spike.
`CLAUDE.md`'s depth policy says a session is a table, and rebuilding it would
teach SQL rather than agents -- so we do not build one. We print one.

Read the output next to `01_agent_loop/from_scratch/agent.py`, where you built a
`messages` list by hand and appended to it after every turn. You are about to see
the same list, produced by a library, with the same shapes in it.

    Chapter 1        messages.append({"role": "user", "content": prompt})
    Chapter 4        session=session

Three parts, and part 3 is the one people get wrong in production:

    PART 1   no session       -- the control. The agent cannot do turn 2.
    PART 2   with a session   -- it can, and here is exactly what it read.
    PART 3   session_id       -- the only thing separating two conversations.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any

from agents import Runner, SQLiteSession
from agents.items import ToolCallItem

from packing_agent import Traveller, agent

TURNS = [
    "Pack two t-shirts, they're 0.2 kg each.",
    "Add two more of those.",
    "What's in the bag?",
]

# THIS DEMO NEEDS A PACER, AND THE REASON IS A DIFFERENT LIMIT FROM THE ONE THE
# GOLDEN DATASETS FIGHT. Written down because the first run of this file died on
# it, and because the two are constantly confused:
#
#   GenerateRequestsPerMinutePerProjectPerModel-FreeTier   15  / minute
#   GenerateRequestsPerDayPerProjectPerModel-FreeTier      500 / day
#
# Seven runs fired back to back is ~15 requests inside forty seconds, which is
# the per-MINUTE wall. `check_expenses.py` never hits it (it pauses 60s between
# cases) and hits the per-DAY one instead. Same status code, same exception
# class, completely different fix -- one needs a sleep, the other needs a
# different model. **Read the quotaId in a 429 before you decide which.**
PACE_SECONDS = 10.0


async def pace() -> None:
    """Stay under the per-minute limit. Free tier only; delete it on a paid key."""
    await asyncio.sleep(PACE_SECONDS)


def show_items(items: list[Any], *, indent: str = "    ") -> None:
    """
    Print a session's stored items the way you would read them in a debugger.

    Deliberately not `pprint`. The point is the SHAPE of each entry -- role,
    type, and how tool calls and their outputs are two separate items rather
    than one -- and pretty-printed JSON buries that under punctuation.
    """
    for index, item in enumerate(items):
        role = item.get("role") or item.get("type") or "?"
        content = item.get("content") or item.get("output") or item.get("arguments") or ""
        if isinstance(content, list):
            content = " ".join(str(part.get("text", part)) for part in content)
        text = str(content).replace("\n", " ")
        if len(text) > 68:
            text = text[:65] + "..."
        name = item.get("name")
        label = f"{role}:{name}" if name else str(role)
        print(f"{indent}[{index:>2}] {label:<28} {text}")


def show_calls(result: Any, indent: str = "        ") -> None:
    """Print the tool calls a run made. The route, not just the destination."""
    for item in result.new_items:
        if isinstance(item, ToolCallItem):
            name = getattr(item.raw_item, "name", "?")
            args = getattr(item.raw_item, "arguments", "")
            print(f"{indent}-> {name}({args})")


async def part_1_no_session() -> None:
    """
    THE CONTROL, AND THE TRAP UNDERNEATH IT.

    Part 1a is the control this chapter needs: no session, and a FRESH context
    per run, so nothing at all carries over. Part 1b changes exactly one thing --
    it reuses the context object -- and the agent starts looking like it
    remembers again.

    Part 1b was not planned. It is what the first version of this file did by
    accident, and the output was so convincing that it nearly shipped as proof
    that sessions were unnecessary. It is kept, deliberately, because a student
    is going to make the same mistake and needs to have seen it named.
    """
    print("=" * 78)
    print("PART 1a - NO SESSION, FRESH CONTEXT. The true control.")
    print("=" * 78)

    for prompt in TURNS[:2]:
        traveller = Traveller(name="Control", bag_limit_kg=20.0)
        result = await Runner.run(agent, prompt, context=traveller)
        print(f"  USER  : {prompt}")
        show_calls(result)
        print(f"  AGENT : {result.final_output}")
        print(f"  bag   : {traveller.packed}")
        await pace()
    print(
        "\n  Turn 2 said 'two more of those'. There is no 'those' -- no transcript,\n"
        "  and an empty bag. Whatever it did, it did not do it from memory."
    )

    print("\n" + "=" * 78)
    print("PART 1b - NO SESSION, SHARED CONTEXT. Watch this carefully.")
    print("=" * 78)

    traveller = Traveller(name="Control", bag_limit_kg=20.0)
    for prompt in TURNS[:2]:
        result = await Runner.run(agent, prompt, context=traveller)
        print(f"  USER  : {prompt}")
        show_calls(result)
        print(f"  AGENT : {result.final_output}")
        await pace()
    print(f"\n  bag contents: {traveller.packed}")
    print(
        "\n  STILL NO SESSION. The model saw no previous turn. And yet the second\n"
        "  run frequently recovers the word 't-shirt' -- because a tool can read\n"
        "  the context, the context still holds the bag, and 'those' resolves\n"
        "  through show_list() instead of through memory.\n"
        "\n  That is state leaking through the OTHER primitive, and it is the single\n"
        "  most common way these two get confused. It is not memory: the agent\n"
        "  cannot recover anything the tools do not expose, cannot tell you what\n"
        "  you ASKED, and cannot tell you what it REFUSED. Part 2 can do all three."
    )


async def part_2_with_session() -> None:
    print("\n" + "=" * 78)
    print("PART 2 - WITH A SESSION. Same agent, same prompts, one extra argument.")
    print("=" * 78)

    traveller = Traveller(name="Faraz", bag_limit_kg=20.0)
    session = SQLiteSession("trip_istanbul")  # ':memory:' by default

    for number, prompt in enumerate(TURNS, start=1):
        result = await Runner.run(agent, prompt, context=traveller, session=session)
        stored = await session.get_items()
        print(f"\n  TURN {number}")
        print(f"  USER  : {prompt}")
        print(f"  AGENT : {result.final_output}")
        print(f"  session now holds {len(stored)} items")
        await pace()

    print(f"\n  bag contents: {traveller.packed}")

    print("\n" + "-" * 78)
    print("  EVERY ITEM THE SESSION STORED")
    print("-" * 78)
    show_items(await session.get_items())

    print(
        "\n  Compare with 01_agent_loop/from_scratch/agent.py. Same list, same\n"
        "  shapes, same growth pattern. You built that by hand in Chapter 1;\n"
        "  `session=session` is the SDK doing the appending for you.\n"
        "\n  Note what is NOT in the list: the word 'Faraz'. That is the context,\n"
        "  and no tool revealed it this run. See context_demo.py."
    )

    print("\n  Raw JSON of item 0, so you can see there is no magic in it:")
    print(f"    {json.dumps((await session.get_items())[0])[:200]}")


async def part_3_session_id_is_the_boundary() -> None:
    print("\n" + "=" * 78)
    print("PART 3 - session_id IS THE BOUNDARY. It is a string. That is all it is.")
    print("=" * 78)

    traveller = Traveller(name="Faraz", bag_limit_kg=20.0)
    trip_a = SQLiteSession("trip_istanbul_2")
    trip_b = SQLiteSession("trip_hunza")

    await Runner.run(agent, "Pack a jacket, 1.2 kg.", context=traveller, session=trip_a)
    await pace()
    result = await Runner.run(agent, "Add two more of those.", context=traveller, session=trip_b)

    print("  trip_istanbul_2 was told about a jacket.")
    print("  trip_hunza then heard only: 'Add two more of those.'")
    print(f"  AGENT (trip_hunza): {result.final_output}")
    print(f"\n  trip_istanbul_2 items : {len(await trip_a.get_items())}")
    print(f"  trip_hunza items      : {len(await trip_b.get_items())}")
    print(
        "\n  Two conversations, one agent, no leakage -- because the ids differ.\n"
        "  Now read that sentence backwards, which is the version that ships bugs:\n"
        "  two conversations that SHARE an id are one conversation, and nothing in\n"
        "  the SDK will tell you. If your session_id is built from a username, a\n"
        "  user with two browser tabs is one confused conversation. If it is built\n"
        "  from a customer-supplied string, one customer can read another's."
    )


async def main() -> None:
    await part_1_no_session()
    await part_2_with_session()
    await part_3_session_id_is_the_boundary()


if __name__ == "__main__":
    asyncio.run(main())
