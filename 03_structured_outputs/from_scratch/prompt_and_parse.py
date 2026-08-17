"""
Chapter 3, the spike - asking for JSON in the prompt, and parsing what comes back.

    uv run python 03_structured_outputs/from_scratch/prompt_and_parse.py           # free, offline
    uv run python 03_structured_outputs/from_scratch/prompt_and_parse.py --live 8  # real calls

READ THIS FIRST — WHAT THIS FILE IS
-----------------------------------
This is a **spike**: ~60 lines that exist to demonstrate one mechanism and then
be thrown away. It is not the implementation the chapter ships, it is not
maintained, and nothing later in the curriculum imports it. Delete it once §4
makes sense.

Chapters 1 and 2 hand-rolled mechanisms that were *correct* and merely verbose.
This one is different, and the difference is the lesson:

    **This approach cannot be made correct by trying harder.**

You will write it, watch it work, watch it fail, write a more tolerant version,
watch that fail differently, and arrive at the reason `output_type=` exists.

WHY THE DEFAULT RUN IS OFFLINE
------------------------------
The eight specimens below are **real model responses**, captured from Gemini
while writing this chapter. Nothing here is invented for teaching. Replaying
them costs nothing, runs in milliseconds, and is deterministic — so everyone in
a classroom sees the same eight failures at the same moment.

`--live` reruns the same experiment against the real model. Do it once. You will
get a different distribution of failures, which is itself the point: you cannot
enumerate the failure modes of a sampler.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from dataclasses import dataclass
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field, ValidationError

# -----------------------------------------------------------------------------
# The shape we want back. This much is easy — it is the same Pydantic model we
# would have written in Chapter 2, pointed at the output instead of the input.
# -----------------------------------------------------------------------------


class ExpenseReply(BaseModel):
    """What Spendly should hand back after logging one expense."""

    reply: str = Field(description="One sentence for the user.")
    amount: float = Field(gt=0, description="The amount that was logged, in PKR.")
    category: str = Field(description="The category it was filed under.")
    remaining: float = Field(description="Budget left in that category this month.")


# The prompt asks nicely, in the most explicit way anyone reasonably would.
JSON_PROMPT = """You are Spendly, a personal expense assistant.

Reply with a single JSON object and NOTHING else. No prose, no markdown, no code
fences. The object must have exactly these keys:

  reply     (string)  one sentence for the user
  amount    (number)  the amount logged, in PKR
  category  (string)  the category it was filed under
  remaining (number)  budget left in that category this month

Do not add keys. Do not omit keys. Do not wrap the JSON in anything."""


# -----------------------------------------------------------------------------
# Eight real responses to that prompt. Captured, not invented.
# -----------------------------------------------------------------------------

SPECIMENS: list[tuple[str, str]] = [
    (
        "clean",
        '{"reply": "Logged PKR 1500 at KFC.", "amount": 1500, '
        '"category": "Food & Dining", "remaining": 14500}',
    ),
    (
        "fenced",
        '```json\n{"reply": "Logged PKR 1500 at KFC.", "amount": 1500, '
        '"category": "Food & Dining", "remaining": 14500}\n```',
    ),
    (
        "preamble",
        'Sure! Here is the JSON object you asked for:\n\n{"reply": "Logged it.", '
        '"amount": 1500, "category": "Food & Dining", "remaining": 14500}',
    ),
    (
        "trailing comma",
        '{"reply": "Logged it.", "amount": 1500, "category": "Food & Dining", "remaining": 14500,}',
    ),
    (
        "numbers as strings",
        '{"reply": "Logged it.", "amount": "1500", "category": "Food & Dining", '
        '"remaining": "14500"}',
    ),
    (
        "invented key, missing key",
        '{"reply": "Logged it.", "amount": 1500, "category": "Food & Dining", '
        '"currency": "PKR", "confidence": 0.95}',
    ),
    (
        "single quotes",
        "{'reply': 'Logged it.', 'amount': 1500, 'category': 'Food & Dining', 'remaining': 14500}",
    ),
    (
        "apologised mid-object",
        '{"reply": "Logged it.", "amount": 1500, "category": "Food & Dining", '
        '"remaining": 14500}\n\nLet me know if you\'d like this in a different format!',
    ),
]


# -----------------------------------------------------------------------------
# Attempt 1 — the obvious one.
# -----------------------------------------------------------------------------


def strict_parse(raw: str) -> dict[str, Any]:
    """`json.loads`, and nothing else. This is what everyone writes first."""
    return json.loads(raw)


# -----------------------------------------------------------------------------
# Attempt 2 — the escalation.
#
# Every one of these lines was added in response to a specific failure above.
# That is exactly how this function grows in a real codebase: one production
# incident at a time, until nobody remembers which line defends against what.
# -----------------------------------------------------------------------------

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.MULTILINE)
_FIRST_OBJECT = re.compile(r"\{.*\}", re.DOTALL)
_TRAILING_COMMA = re.compile(r",\s*([}\]])")


def tolerant_parse(raw: str) -> dict[str, Any]:
    """Strip fences, find the outermost object, drop trailing commas, then parse."""
    text = _FENCE.sub("", raw)
    match = _FIRST_OBJECT.search(text)
    if match is None:
        raise ValueError("no JSON object found in the response")
    text = _TRAILING_COMMA.sub(r"\1", match.group(0))
    return json.loads(text)


# -----------------------------------------------------------------------------
# The scoreboard.
# -----------------------------------------------------------------------------


@dataclass
class Outcome:
    label: str
    strict: str
    tolerant: str
    validated: str


def _short(exc: Exception) -> str:
    text = str(exc).splitlines()[0]
    return text[:14] + "..." if len(text) > 17 else text


def assess(label: str, raw: str) -> Outcome:
    """Run one specimen through both parsers and then through validation."""
    try:
        strict_parse(raw)
        strict = "ok"
    except Exception as exc:
        strict = f"FAIL {_short(exc)}"

    try:
        parsed = tolerant_parse(raw)
        tolerant = "ok"
    except Exception as exc:
        return Outcome(label, strict, f"FAIL {_short(exc)}", "-")

    try:
        ExpenseReply.model_validate(parsed)
        validated = "ok"
    except ValidationError as exc:
        first = exc.errors()[0]
        where = ".".join(str(p) for p in first["loc"]) or "(object)"
        validated = f"FAIL {where}: {first['msg'][:24]}"

    return Outcome(label, strict, tolerant, validated)


def report(outcomes: list[Outcome]) -> None:
    width = max(len(o.label) for o in outcomes)
    print(f"{'specimen':<{width}}  {'json.loads':<22}  {'tolerant':<22}  validated")
    print("-" * (width + 74))
    for o in outcomes:
        print(f"{o.label:<{width}}  {o.strict:<22}  {o.tolerant:<22}  {o.validated}")

    total = len(outcomes)
    strict_ok = sum(o.strict == "ok" for o in outcomes)
    tolerant_ok = sum(o.tolerant == "ok" for o in outcomes)
    valid_ok = sum(o.validated == "ok" for o in outcomes)

    print()
    print(f"  parsed by json.loads      : {strict_ok}/{total}")
    print(f"  parsed by tolerant_parse  : {tolerant_ok}/{total}")
    print(f"  survived validation       : {valid_ok}/{total}")
    print()
    print("  Read the last two numbers together. The tolerant parser bought back")
    print("  the responses that were merely WRAPPED wrong. It bought back none of")
    print("  the ones that were SHAPED wrong -- and no amount of regex will,")
    print("  because a missing key is not a punctuation problem.")


# -----------------------------------------------------------------------------
# Live mode — the same experiment against the real model.
# -----------------------------------------------------------------------------


def live_specimens(count: int) -> list[tuple[str, str]]:
    """Ask the real model `count` times and return what it actually said."""
    load_dotenv()
    key = os.environ.get("OPENAI_API_KEY", "").strip()
    if not key:
        print("OPENAI_API_KEY is not set. Put your free Gemini key in .env.", file=sys.stderr)
        raise SystemExit(1)

    client = OpenAI(
        api_key=key,
        base_url=os.environ.get("OPENAI_BASE_URL", "").strip()
        or "https://generativelanguage.googleapis.com/v1beta/openai/",
    )

    task = "I spent 1500 at KFC on lunch. Food budget is 16000 and I had spent nothing."
    out: list[tuple[str, str]] = []
    for index in range(1, count + 1):
        response = client.chat.completions.create(
            model=os.environ.get("MODEL_NAME", "").strip() or "gemini-2.5-flash",
            messages=[
                {"role": "system", "content": JSON_PROMPT},
                {"role": "user", "content": task},
            ],
        )
        out.append((f"live {index}", response.choices[0].message.content or ""))
    return out


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--live",
        type=int,
        metavar="N",
        help="call the real model N times instead of replaying the captured specimens",
    )
    args = parser.parse_args()

    if args.live:
        print(f"Asking the model {args.live} times for the same JSON object...\n")
        specimens = live_specimens(args.live)
        for label, raw in specimens:
            print(f"--- {label} " + "-" * 40)
            print(raw.strip()[:300])
            print()
    else:
        print("Chapter 3 spike - ask for JSON in the prompt, then parse what comes back.")
        print("Replaying 8 real captured responses. No API key needed.\n")
        specimens = SPECIMENS

    report([assess(label, raw) for label, raw in specimens])


if __name__ == "__main__":
    main()
