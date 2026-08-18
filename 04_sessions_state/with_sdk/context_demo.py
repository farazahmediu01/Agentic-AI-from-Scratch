"""
OBSERVE: what a context is, and what the model can never see.

    uv run python 04_sessions_state/with_sdk/context_demo.py

A session is what the agent REMEMBERS. A context is what you HAND it.

`session_demo.py` showed the first half by printing a transcript. This shows the
second half, and the claim it is making is stronger than "context is convenient":

    The context object is never serialised, never sent, and never stored.
    A tool can read it. The model cannot -- until a tool tells it.

    PART 1   the schemas    -- free. What the model is told a tool takes.
    PART 2   two travellers -- same agent, same prompt, different right answer.
    PART 3   the leak       -- free-ish. Where a context ends up once a tool
                               returns part of it, and why that is a decision.
"""

from __future__ import annotations

import asyncio
import json

from agents import Runner, SQLiteSession
from agents.tool import FunctionTool

from packing_agent import Traveller, add_item, agent, remaining_allowance, whoami

PACE_SECONDS = 10.0

QUESTION = "Who am I packing for, and how much room do I have left?"


def show_schema(tool: FunctionTool) -> None:
    schema = tool.params_json_schema
    properties = list(schema.get("properties", {}))
    print(f"  {tool.name:<22} model is told about: {properties or '(no arguments)'}")


async def part_1_the_schemas() -> None:
    """Free. No model calls."""
    print("=" * 78)
    print("PART 1 - WHAT THE MODEL IS TOLD EACH TOOL TAKES")
    print("=" * 78)

    for tool in (whoami, add_item, remaining_allowance):
        assert isinstance(tool, FunctionTool)
        show_schema(tool)

    print(
        "\n  Every one of those functions declares `ctx: RunContextWrapper[Traveller]`\n"
        "  as its FIRST parameter, and not one of them mentions it here. The SDK\n"
        "  strips a leading RunContextWrapper before generating the schema.\n"
        "\n  That asymmetry is the whole primitive. The model decides WHAT to ask\n"
        "  for; your application decides WHOSE data answers. Neither can do the\n"
        "  other's job, and neither can see the other's input -- which means a\n"
        "  prompt injection cannot reach `ctx.context` no matter how it is worded.\n"
        "  There is no argument to poison."
    )
    print(f"\n  whoami's full schema: {json.dumps(whoami.params_json_schema)}")


async def part_2_two_travellers() -> tuple[SQLiteSession, SQLiteSession]:
    print("\n" + "=" * 78)
    print("PART 2 - ONE AGENT, ONE PROMPT, TWO RIGHT ANSWERS")
    print("=" * 78)
    print(f"  prompt (identical for both): {QUESTION!r}\n")

    faraz = Traveller(name="Faraz", bag_limit_kg=20.0, packed=[("laptop", 1.4)])
    ayesha = Traveller(name="Ayesha", bag_limit_kg=7.0, packed=[("laptop", 1.4)])

    sessions: list[SQLiteSession] = []
    for traveller in (faraz, ayesha):
        session = SQLiteSession(f"trip_{traveller.name.lower()}")
        result = await Runner.run(agent, QUESTION, context=traveller, session=session)
        print(
            f"  context = Traveller(name={traveller.name!r}, bag_limit_kg={traveller.bag_limit_kg})"
        )
        print(f"  AGENT   : {result.final_output}\n")
        sessions.append(session)
        await asyncio.sleep(PACE_SECONDS)

    print(
        "  Same agent object. Same instructions. Same tools. Same prompt string.\n"
        "  The only difference between those two runs is one keyword argument, and\n"
        "  it produced two different, both-correct answers.\n"
        "\n  Now consider the alternative you have almost certainly written before:\n"
        "  interpolating the allowance into the system prompt. It works, and it\n"
        "  costs three things -- the number becomes tokens you pay for on every\n"
        "  turn, it is visible to anyone who can make the model repeat its own\n"
        "  instructions, and the model is free to round it."
    )
    return sessions[0], sessions[1]


async def part_3_the_leak(faraz_session: SQLiteSession) -> None:
    print("\n" + "=" * 78)
    print("PART 3 - A CONTEXT IS INVISIBLE UNTIL A TOOL REVEALS IT")
    print("=" * 78)

    stored = json.dumps(await faraz_session.get_items())
    print(f"  PART 2's session for Faraz: {len(await faraz_session.get_items())} items")
    print(f"  does the transcript contain the string 'Faraz'? -> {'Faraz' in stored}")

    # A run whose prompt gives the model no reason to ask who it is talking to.
    quiet = Traveller(name="Faraz", bag_limit_kg=20.0)
    quiet_session = SQLiteSession("trip_quiet")
    await Runner.run(agent, "Pack a jacket, 1.2 kg.", context=quiet, session=quiet_session)
    quiet_stored = json.dumps(await quiet_session.get_items())
    print(f"\n  a run that never called whoami: {len(await quiet_session.get_items())} items")
    print(f"  does THAT transcript contain 'Faraz'? -> {'Faraz' in quiet_stored}")

    print(
        "\n  Both answers matter, and the second is the one people assume without\n"
        "  checking. The context did not leak on its own -- it left the process\n"
        "  because a tool returned it, and a tool's return value is stored in the\n"
        "  session like everything else.\n"
        "\n  So the rule is not 'a context is safe'. It is:\n"
        "\n      A context is private until a tool returns part of it.\n"
        "      After that it is in the transcript, permanently, and it is\n"
        "      re-sent on every subsequent turn.\n"
        "\n  Which makes 'what does this tool return?' a security question, not\n"
        "  just an API design one. Returning the whole context object from a\n"
        "  convenience tool is how a support agent ends up with a customer's\n"
        "  internal risk score in a transcript somebody later exports.\n"
        "\n  And the rule underneath it, which Chapter 8 will make load-bearing:\n"
        "  never put a credential in either place. Not in the session, because it\n"
        "  is sent to the model; not returned from a tool, for the same reason.\n"
        "  A context may HOLD a database handle -- it must never HAND one out."
    )


async def main() -> None:
    await part_1_the_schemas()
    faraz_session, _ = await part_2_two_travellers()
    await part_3_the_leak(faraz_session)


if __name__ == "__main__":
    asyncio.run(main())
