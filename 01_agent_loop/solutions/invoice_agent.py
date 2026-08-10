"""
Chapter 1 Project solution — the Freelance Invoice Agent.

Run:  uv run python 01_agent_loop/solutions/invoice_agent.py

Everything the chapter taught, assembled:
  loop + tool schemas + registry + chaining + system prompt + error recovery
  + iteration ceiling + run instrumentation.
"""

from __future__ import annotations

from invoice_tools import TOOL_REGISTRY, TOOL_SCHEMAS
from loop import run_agent

SYSTEM_PROMPT = (
    "You are an invoicing assistant for a freelance software consultant. "
    "All amounts are in PKR.\n"
    "\n"
    "Hard rules:\n"
    "1. NEVER calculate any number yourself. Every rate, multiplication, sum, "
    "   discount and tax must come from a tool result. If you cannot get a number "
    "   from a tool, say so instead of estimating.\n"
    "2. Order of operations: lookup_rate -> line_total (per role) -> add (into a "
    "   subtotal) -> apply_discount -> apply_tax -> save_invoice.\n"
    "3. The discount and tax arguments to save_invoice are AMOUNTS, not percentages. "
    "   Derive them from the tool results you already have.\n"
    "4. If the client name, the role, or the hours are missing, ASK the user for them. "
    "   Do not invent placeholder values and do not save an incomplete invoice.\n"
    "5. If a role is not on the rate card, tell the user which roles are valid and "
    "   stop. Do not save a file.\n"
    "6. NEVER silently correct a value the user gave you. If a number is "
    "   impossible — negative hours, a negative rate, a percentage above 100 — "
    "   do NOT clean it up and continue. Stop, say what is wrong, and ask the "
    "   user to confirm the correct value. Passing a 'fixed' value to a tool is "
    "   the worst possible outcome: it produces a confident, wrong invoice.\n"
    "7. Once the invoice is saved, stop calling tools and reply with a one-line "
    "   confirmation plus a Subtotal / Discount / Tax / Total summary."
)

# Why rule 6 exists — read this, it is the most important lesson in the chapter.
#
# `line_total` raises on negative hours, so the tool was "guarded". The first
# version of this agent still billed Delta Co for -3 hours: the model normalised
# -3 to 3 *before* calling the tool, so the guard never fired. The invoice was
# saved, confidently, and wrong.
#
# A validation check only protects you if the bad value actually reaches it.
# The model sits upstream of every tool guard you write, and models are trained
# to be helpful — which includes "fixing" input that looks like a typo. So the
# guard has to exist at BOTH layers: an instruction where the decision is made,
# and a raise where the work is done. Defence in depth, and Step 6's guardrails
# are the systematic version of this idea.

TASK = (
    "I did 12 hours of backend work and 6.5 hours of UI design for Acme Corp this "
    "month. Apply the 10% loyalty discount and 5% tax. Save the invoice."
)


if __name__ == "__main__":
    print(f"USER TASK:\n  {TASK}")
    print("=" * 72)

    run = run_agent(
        user_message=TASK,
        tool_registry=TOOL_REGISTRY,
        tool_schemas=TOOL_SCHEMAS,
        system_prompt=SYSTEM_PROMPT,
    )

    print("=" * 72)
    print(f"\nFINAL ANSWER:\n{run.final_answer}")
    print(run.summary())

    # Expected for this task:
    #   backend    12.0h x 6500 = 78,000.00
    #   ui design   6.5h x 5500 = 35,750.00
    #   subtotal                 113,750.00
    #   -10% discount            -11,375.00  -> 102,375.00
    #   +5% tax                    5,118.75  -> 107,493.75
