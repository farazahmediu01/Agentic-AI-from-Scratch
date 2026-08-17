"""
Spendly Lite v3 — the output contract.

This is the chapter, in one file. Chapter 2 put a contract on the way IN; this
puts one on the way OUT.

WHY FOUR BRANCHES AND NOT ONE MODEL
-----------------------------------
Look at Chapter 2's golden dataset and read it as a list of OUTCOMES rather than
a list of prompts. There are exactly four things Spendly can honestly do:

    log something          -> Logged
    answer a question      -> Reported
    ask for what's missing -> NeedMoreInfo
    refuse bad data        -> Refused

The dataset was already classifying every run into one of those four. It just
had to do it by searching the final sentence for substrings -- `"logged" in
answer.lower()`, `"?" in answer`. That is a classifier built out of `str.find`,
and it is wrong in both directions: "I could not log that" contains "logged",
and a helpful closing "Anything else?" contains a question mark.

Making the four outcomes into four TYPES deletes the classifier. `reply.refused
is not None` is not a heuristic about wording. It is the shape the model chose.

THE TRAP, AND WHY THE VALIDATOR AT THE BOTTOM EXISTS
----------------------------------------------------
A union expressed as four optional fields has two failure modes the type system
cannot rule out: the model can set NONE of them, or it can set TWO.

`output_type=` guarantees you get a `SpendlyReply`. It does not guarantee the
`SpendlyReply` means anything. That is the same lesson as Chapter 2 section 7b,
one level up: a schema constrains SHAPE, and shape is not truth.

So `exactly_one_branch` below is a check that runs AFTER the model and cannot be
talked out of its job. Notice where it had to live -- not in the type, not in the
prompt, but in code that runs on the result. That is a guardrail, and it is why
guardrails are a separate primitive rather than a longer prompt.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

# Imported from Chapter 2's solutions. The spine is ONE codebase now -- see the
# taper rule in CLAUDE.md. Chapter 2's storage and tools are carried forward
# unchanged, and the fact that they needed no changes is itself the point: a
# well-drawn boundary survives the next chapter.
import _bootstrap  # noqa: F401  -- must precede every spine import; see _bootstrap.py
from expense_store import Category

__all__ = [
    "Logged",
    "NeedMoreInfo",
    "Refused",
    "Reported",
    "SpendlyReply",
]


class Logged(BaseModel):
    """An expense was written to the ledger."""

    reply: str = Field(description="One sentence confirming what was recorded.")
    vendor: str = Field(description="The vendor exactly as the user gave it.")
    amount: float = Field(gt=0, description="The amount recorded, in PKR.")
    category: Category = Field(description="The category it was filed under.")
    remaining: float | None = Field(
        default=None,
        description="Budget left in that category after this expense, if the user asked.",
    )


class Reported(BaseModel):
    """A question about existing spending was answered. Nothing was written."""

    reply: str = Field(description="One sentence answering the question.")
    category: Category | None = Field(
        default=None, description="The category the figures refer to, if it was about one."
    )
    spent: float | None = Field(default=None, description="Amount spent, if reported.")
    budget: float | None = Field(default=None, description="The budget, if reported.")
    remaining: float | None = Field(default=None, description="Budget remaining, if reported.")


class NeedMoreInfo(BaseModel):
    """
    Something required was missing, so nothing happened.

    `missing` is the field that makes this worth having as a type. A prose
    question is unassertable; `missing == ["amount"]` is a fact you can count
    across a hundred runs to find out what your agent asks for most often.
    """

    question: str = Field(description="The single question to put to the user.")
    missing: list[Literal["vendor", "amount", "category", "date"]] = Field(
        description="Which required values were not supplied."
    )


class Refused(BaseModel):
    """
    The user supplied something Spendly must not act on, and must not silently fix.

    This is Chapter 2 section 7b as a type. A negative amount, a future date, a
    category that does not exist: the failure there was that the model quietly
    CORRECTED the value and reported success. Giving refusal its own shape means
    the honest outcome is a shape the model can reach, instead of a deviation
    from the only shape you allowed it.
    """

    reply: str = Field(description="One sentence explaining what is wrong.")
    reason: Literal["negative_amount", "future_date", "unknown_category", "other"] = Field(
        description="Why the request was refused."
    )
    offending_value: str = Field(description="The value the user gave, echoed back verbatim.")


class SpendlyReply(BaseModel):
    """
    Exactly one branch is set. See the validator for why that is enforced here
    rather than trusted.
    """

    logged: Logged | None = None
    reported: Reported | None = None
    need_more_info: NeedMoreInfo | None = None
    refused: Refused | None = None

    @property
    def branch(self) -> str:
        """Which outcome this is. The whole reason the eval no longer greps."""
        for name in ("logged", "reported", "need_more_info", "refused"):
            if getattr(self, name) is not None:
                return name
        return "none"

    @model_validator(mode="after")
    def exactly_one_branch(self) -> SpendlyReply:
        """
        The check the schema cannot express.

        JSON Schema can say "these four fields are optional objects". It cannot
        say "exactly one of them is non-null" in a way every provider enforces.
        So we say it here, in Python, after the model has spoken.
        """
        set_branches = [
            name
            for name in ("logged", "reported", "need_more_info", "refused")
            if getattr(self, name) is not None
        ]
        if len(set_branches) != 1:
            raise ValueError(
                f"exactly one branch must be set, got {len(set_branches)}: {set_branches or '[]'}"
            )
        return self
