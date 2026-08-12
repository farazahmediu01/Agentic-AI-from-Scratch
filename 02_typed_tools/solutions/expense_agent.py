"""
Spendly Lite v2 — the from-scratch build.

    uv run python 02_typed_tools/solutions/expense_agent.py

READ THIS BEFORE THE PROMPT. It records a mistake, and the mistake is the most
useful thing in the chapter.

The first draft of this file deleted two lines from Chapter 1's prompt:

    "Categories are a fixed set. Never invent one."
    "Never log a negative or zero amount. Do NOT correct the value yourself."

The reasoning sounded right: those are shape rules, `Literal` and `Field(gt=0)`
now enforce them at the boundary, so why ask the model politely for something
the type already guarantees?

Then the golden dataset ran, and the SDK build failed three cases:

    CASE 5  "Log -450 at Imtiaz Supermarket for groceries."
            -> the model logged PKR 450.00 and reported success.

    CASE 7  "Log 3000 at Metro for groceries on 2099-01-01."
            -> rejected once for the future date, then re-called with TODAY
               and reported success.

Neither is a validation failure. `gt=0` worked perfectly -- **no negative number
ever reached the tool.** The model flipped the sign *before* calling, so the
boundary saw a clean, valid, completely fabricated 450.

That is the distinction this chapter has to get exactly right:

    A TYPE stops a bad value from being ACCEPTED.
    A PROMPT stops the model from INVENTING a good one.

They defend against different things and neither substitutes for the other. The
type made the enforcement redundant; it did not make the POLICY redundant. Case
7 is the sharper version: the rejection message literally says "if the correct
value is something the user never told you, ask them for it -- do not invent
it", and the model substituted today's date anyway. One sentence of policy, in
one place, is not enough for a rule that costs a wrong ledger row.

So the deleted lines are back below, and they are marked. A prompt is for
judgement, a type is for shape -- but "never silently correct a value the user
gave you" is judgement, and it was always judgement.
"""

from __future__ import annotations

import expense_store
from expense_tools import ALL_TOOLS
from loop import run_agent

SYSTEM_PROMPT = """You are Spendly, a careful personal expense assistant. All amounts are in PKR.

How to work:
- Use tools for every fact. Never recall a total or a budget from memory.
- Log an expense only when you know the vendor, the amount and the category.
- If something is missing, ask the user. Do not guess and do not use a placeholder.
- Read the tool's own reply before answering. Never claim you logged something
  unless the tool told you it was logged.

NEVER SILENTLY CORRECT THE USER'S DATA. This is the rule that types cannot enforce:
- If the user gives a negative or zero amount, do NOT make it positive. Refuse,
  say why, and ask them to confirm what they actually spent.
- If the user gives a date that cannot be used, do NOT substitute today's date.
  Tell them what is wrong with the date they gave and ask for the real one.
- If the user names a category that does not exist, do NOT pick the closest one.
  Call list_categories and let them choose.
A value that passes validation is not the same as a value the user gave you.

When a tool rejects your arguments:
- Read the error. It names the argument and what was wrong with it.
- Fix it ONLY if the correct value is something the user actually said.
- Otherwise stop and ask. A rejection is not permission to invent a value that
  passes.

Finish with one clear sentence for the user, including the numbers you looked up.
"""


TASK = (
    "I spent 1500 at KFC on lunch today. Log it, then tell me how much of my "
    "food budget is left this month."
)


def main() -> None:
    expense_store.reset(seeded=True)

    print(f"USER TASK:\n  {TASK}")
    print("=" * 72)

    run = run_agent(user_message=TASK, tools=ALL_TOOLS, system_prompt=SYSTEM_PROMPT)

    print("=" * 72)
    print(run.summary())
    print(f"\nFINAL ANSWER:\n{run.final_answer}\n")


if __name__ == "__main__":
    main()
