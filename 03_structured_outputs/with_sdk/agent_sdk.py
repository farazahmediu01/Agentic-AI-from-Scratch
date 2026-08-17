"""
Chapter 3 — the same job, with `output_type=`.

    uv run python 03_structured_outputs/with_sdk/agent_sdk.py

The spike asked the model for JSON and parsed what came back. Three of eight
responses survived `json.loads`. Seven survived a regex-hardened parser. Six
survived validation, and the two that did not could never have been recovered
by better parsing, because they were the wrong SHAPE, not the wrong punctuation.

This file does the same job in one argument:

    Agent(..., output_type=ExpenseReply)

and `result.final_output` is an `ExpenseReply` instance. Not a string that looks
like one. Not a dict you have to check. The typed object, or an exception.

Two demos:

  1. `output_type=ExpenseReply`  — the contract on the way out
  2. `output_type=Reply`         — a UNION, so "I need to ask you something"
                                   is a first-class outcome instead of prose

Demo 2 is the one worth your attention. A single rigid output model is how you
teach an agent to fabricate: if the only shape it can return demands an
`amount`, it will produce an `amount` whether or not you gave it one.
"""

from __future__ import annotations

import asyncio
import json

from agents import Agent, Runner
from pydantic import BaseModel, Field

from shared.models import make_model

MODEL = make_model()


# -----------------------------------------------------------------------------
# Demo 1 — one shape, guaranteed.
# -----------------------------------------------------------------------------


class ExpenseReply(BaseModel):
    """The same model the spike tried to parse its way to."""

    reply: str = Field(description="One sentence for the user.")
    amount: float = Field(gt=0, description="The amount that was logged, in PKR.")
    category: str = Field(description="The category it was filed under.")
    remaining: float = Field(description="Budget left in that category this month.")


# -----------------------------------------------------------------------------
# Demo 2 — the union.
#
# Chapter 2 taught the agent to ask instead of guessing with a line in the system
# prompt. That was a REQUEST. This makes it a TYPE: "I need more information" is
# now one of the shapes the agent is allowed to return, so choosing it is a
# normal outcome rather than a deviation from the format you demanded.
# -----------------------------------------------------------------------------


class Logged(BaseModel):
    """Everything was known and the expense was recorded."""

    kind: str = Field(default="logged", description="Always the literal 'logged'.")
    reply: str
    amount: float = Field(gt=0)
    category: str


class NeedMoreInfo(BaseModel):
    """Something required was missing. Nothing was recorded."""

    kind: str = Field(default="need_more_info", description="Always 'need_more_info'.")
    question: str = Field(description="The single question to ask the user.")
    missing: list[str] = Field(description="Which fields are missing, e.g. ['amount'].")


class Reply(BaseModel):
    """
    The union, expressed as one model with two optional branches.

    A bare `Logged | NeedMoreInfo` also works with the SDK, but providers differ
    in how well they handle `anyOf` at the top level of a strict schema. One
    wrapper model with two optional fields is the portable spelling, and it
    survives the swap from Gemini to OpenAI unchanged.
    """

    logged: Logged | None = Field(default=None, description="Set when the expense was recorded.")
    need_more_info: NeedMoreInfo | None = Field(
        default=None, description="Set when something required was missing."
    )


INSTRUCTIONS = """You are Spendly, a personal expense assistant. Amounts are in PKR.

The user's Food & Dining budget is 16000 and they have spent nothing this month.

Never invent a value the user did not give you. If the amount, the vendor or the
category is missing, do not guess and do not use a placeholder."""


async def demo_single_shape() -> None:
    print("=" * 72)
    print("DEMO 1 - output_type=ExpenseReply")
    print("=" * 72)

    agent = Agent(
        name="Spendly (typed reply)",
        instructions=INSTRUCTIONS,
        model=MODEL,
        output_type=ExpenseReply,
    )

    result = await Runner.run(agent, "I spent 1500 at KFC on lunch. Log it.")
    out = result.final_output

    print(f"type(result.final_output) : {type(out).__name__}")
    print(f"  .reply     -> {out.reply}")
    print(f"  .amount    -> {out.amount!r}   ({type(out.amount).__name__})")
    print(f"  .category  -> {out.category!r}")
    print(f"  .remaining -> {out.remaining!r}")
    print()
    print("Note what did NOT happen: no json.loads, no fence stripping, no regex,")
    print("no retry loop. And `.amount` is a float, so you can do arithmetic with")
    print("it on the next line without asking whether it might be the string '1500'.")
    print()


async def demo_union() -> None:
    print("=" * 72)
    print("DEMO 2 - a union, so 'I have to ask' is a shape and not a deviation")
    print("=" * 72)

    agent = Agent(
        name="Spendly (union reply)",
        instructions=INSTRUCTIONS,
        model=MODEL,
        output_type=Reply,
    )

    prompts = [
        "I spent 1500 at KFC on lunch. Log it.",
        "Log my lunch at KFC.",  # no amount — the agent must ask
    ]

    for prompt in prompts:
        result = await Runner.run(agent, prompt)
        reply = result.final_output

        print(f"\nUSER: {prompt}")
        if reply.logged is not None:
            print(f"  -> LOGGED   amount={reply.logged.amount} cat={reply.logged.category!r}")
            print(f"     {reply.logged.reply}")
        elif reply.need_more_info is not None:
            print(f"  -> ASKING   missing={reply.need_more_info.missing}")
            print(f"     {reply.need_more_info.question}")
        else:
            print("  -> neither branch was set. See README §8.")

    print()
    print("The second prompt is the one that matters. In Chapter 2 the agent could")
    print("only ask by writing a sentence, and your eval had to grep for a question")
    print("mark. Now 'I need to ask' is `reply.need_more_info is not None` - a fact")
    print("you can assert on, count, log, and route.")
    print()


def show_schema() -> None:
    """What actually goes over the wire — the contract, generated from the model."""
    print("=" * 72)
    print("The JSON Schema the SDK sends for ExpenseReply")
    print("=" * 72)
    print(json.dumps(ExpenseReply.model_json_schema(), indent=2))
    print()
    print("Same three moves as Chapter 2's @tool - read the annotations, build a")
    print("validator, publish the schema. Pointed at the output instead of the input.")
    print()


async def main() -> None:
    show_schema()
    await demo_single_shape()
    await demo_union()


if __name__ == "__main__":
    asyncio.run(main())
