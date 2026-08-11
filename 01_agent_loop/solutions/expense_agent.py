"""
Spendly Lite v1 — from-scratch build (Layers 2 + 6).

Run:  uv run python 01_agent_loop/solutions/expense_agent.py

This is the chapter project assembled on your own loop: tools, hand-written
schemas, a registry, a system prompt, chaining, error recovery, an iteration
ceiling, and a run summary.

`expense_agent_sdk.py` is the same agent on the OpenAI Agents SDK. The same
check harness grades both.
"""

from __future__ import annotations

from expense_tools import TOOL_REGISTRY, TOOL_SCHEMAS
from loop import run_agent

SYSTEM_PROMPT = (
    "You are Spendly Lite, a personal expense assistant. All amounts are in PKR.\n"
    "\n"
    "Hard rules:\n"
    "1. NEVER calculate a total or a remaining budget yourself. Every number you "
    "   report must come from a tool result. If a tool did not give it to you, you "
    "   do not know it.\n"
    "2. To answer 'how much is left in my <category> budget', call get_budget and "
    "   month_total, then subtract(budget, month_total). Remaining budget is "
    "   budget MINUS EVERYTHING SPENT THIS MONTH — never budget minus the single "
    "   expense you just logged.\n"
    "3. ORDER MATTERS. If the user asks you to log an expense AND report a budget, "
    "   call log_expense FIRST, then month_total. month_total read before the write "
    "   is a stale number and will not include the expense you just recorded.\n"
    "4. Log an expense ONLY when you know the vendor, the amount, and a valid "
    "   category. If any of the three is missing, ask the user for it. Never "
    "   invent a vendor, an amount, or a category.\n"
    "5. NEVER silently correct a value the user gave you. A negative amount, an "
    "   impossible date, or an unknown category means you STOP and ask. Quietly "
    "   'fixing' input produces a confident, wrong ledger — the worst outcome "
    "   this system can produce.\n"
    "6. If the category is invalid, call list_categories and offer the real "
    "   options. Do not log anything until the user picks one.\n"
    "7. When the work is done, stop calling tools and reply in two lines or less. "
    "   Include the amounts you were given by tools."
)

TASK = (
    "I spent 1500 at KFC on lunch today. Log it, then tell me how much of my "
    "food budget is left this month."
)


if __name__ == "__main__":
    print(f"USER: {TASK}")
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

    # With the seeded store (7,500 already spent on Food & Dining this month):
    #   log 1500 -> month_total = 9,000 -> budget 25,000 -> remaining 16,000
