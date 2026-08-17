"""
Pydantic - turning "I hope this data is right" into "it is, or I know why".

    uv run python 00_python_for_agents/examples/pydantic_lab.py

WHY THIS MATTERS FOR AGENTS
---------------------------
Every value an agent hands your code was written by a language model. It is
text, it is untrusted, and it is *usually* fine -- which is the dangerous kind
of wrong, because "usually" is doing enormous work in a program that writes to a
database.

Pydantic is how this curriculum draws the line between outside and inside. From
Chapter 2 on, every tool argument crosses a Pydantic model on the way in, and
from Chapter 3 every answer crosses one on the way out.
"""

from __future__ import annotations

import json
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

# =============================================================================
# 1. A model is a shape, and shapes can be checked
# =============================================================================


class Booking(BaseModel):
    """One seat reservation, as it might arrive from a form or an API."""

    passenger: str = Field(min_length=1, description="Full name as on the ID.")
    seats: int = Field(ge=1, le=9, description="How many seats, 1 to 9.")
    cabin: Literal["economy", "business", "first"] = Field(description="Cabin class.")
    email: str | None = Field(default=None, description="Optional contact email.")


def demo_happy_path() -> None:
    payload = '{"passenger": "Faraz Ahmed", "seats": 2, "cabin": "business"}'

    booking = Booking.model_validate_json(payload)
    print(f"  parsed -> {booking}")
    print(f"  booking.seats is a real int -> {booking.seats + 1}")
    print(f"  email defaulted to -> {booking.email!r}")


# =============================================================================
# 2. What a rejection actually gives you
# =============================================================================


def demo_rejection() -> None:
    bad = '{"passenger": "", "seats": 40, "cabin": "premium"}'

    try:
        Booking.model_validate_json(bad)
    except ValidationError as exc:
        print(f"  {len(exc.errors())} problems, all reported at once:\n")
        for error in exc.errors():
            where = ".".join(str(p) for p in error["loc"])
            print(f"    {where:<10} {error['msg']}  (you sent: {error.get('input')!r})")

    print()
    print("  Three things worth noticing:")
    print("    - it found ALL the problems, not just the first")
    print("    - each one names the field, the rule, and the value you sent")
    print("    - nothing after the validation ran, so nothing was half-done")
    print()
    print("  In Chapter 2 you turn exactly this structure into a message a MODEL")
    print("  reads and acts on. An error is an instruction when the reader is an")
    print("  agent, and that reframing is most of the chapter.")


# =============================================================================
# 3. Coercion - helpful, until it isn't
# =============================================================================


def demo_coercion() -> None:
    # Models emit JSON, and JSON from a language model puts numbers in quotes
    # more often than you would like. Pydantic quietly fixes it:
    coerced = Booking.model_validate_json(
        '{"passenger": "Ayesha", "seats": "3", "cabin": "economy"}'
    )
    print(f'  seats sent as the string "3" -> {coerced.seats!r} ({type(coerced.seats).__name__})')
    print("  Good. That is a real class of noise handled for you.")
    print()

    # Now the same helpfulness, being a menace:
    sneaky = Booking.model_validate_json(
        '{"passenger": "Ayesha", "seats": true, "cabin": "economy"}'
    )
    print(f"  seats sent as `true`         -> {sneaky.seats!r}")
    print()
    print("  `true` passed a check for a whole number between 1 and 9, and became")
    print("  a perfectly ordinary `1`, because in Python `bool` is a subclass of")
    print("  `int`. No rule was broken. You now have a confirmed booking for one")
    print("  seat that nobody asked for, and nothing anywhere will ever flag it.")
    print()
    print("  This is a REAL bug that this curriculum shipped: Chapter 2 accepted")
    print('  `{"amount": true}` and logged an expense of PKR 1.00. It was caught')
    print("  by a test, not by reading. The fix is a `BeforeValidator`, and you")
    print("  will meet it there.")
    print()
    print("  The lesson to carry: **a library's defaults are somebody else's")
    print("  judgement about your trade-offs.** Lax coercion is right for a model's")
    print("  sloppy JSON and wrong for a money field, and only you know which one")
    print("  you have.")


# =============================================================================
# 4. The model IS the documentation
# =============================================================================


def demo_schema() -> None:
    schema = Booking.model_json_schema()
    print(json.dumps(schema, indent=2)[:700])
    print("  ...")
    print()
    print("  You wrote a class. Pydantic generated a JSON Schema from it -- the")
    print("  types, the ranges, the allowed values, your descriptions.")
    print()
    print("  That generated schema is how a language model is TOLD what a tool")
    print("  takes. One declaration produces the validator and the documentation,")
    print("  and because they come from the same source they cannot drift apart.")
    print("  Chapter 2 is built on this one fact.")


def main() -> None:
    for title, demo in (
        ("1. A model is a shape", demo_happy_path),
        ("2. What a rejection tells you", demo_rejection),
        ("3. Coercion, helpful and harmful", demo_coercion),
        ("4. The model is the documentation", demo_schema),
    ):
        print("=" * 72)
        print(title)
        print()
        demo()
        print()


if __name__ == "__main__":
    main()
