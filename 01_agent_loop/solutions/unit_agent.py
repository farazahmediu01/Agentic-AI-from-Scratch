"""
Exercise 4 solution — the Unit Converter Agent.

Run:  uv run python 01_agent_loop/solutions/unit_agent.py
"""

from __future__ import annotations

from loop import run_agent
from unit_tools import TOOL_REGISTRY, TOOL_SCHEMAS

SYSTEM_PROMPT = (
    "You are a precise unit-conversion assistant.\n"
    "Rules:\n"
    "1. NEVER do a conversion in your head. Always call the matching tool.\n"
    "2. If the user asks for a rounded value, call round_number on the tool's "
    "   output rather than rounding it yourself.\n"
    "3. If no tool exists for a requested unit, say plainly that you cannot "
    "   convert it and list the conversions you do support. Never guess a number.\n"
    "4. When everything is converted, stop calling tools and give one clean summary."
)

TASK = (
    "I'm shipping a 12.5 kg package 340 km, and the warehouse is 31 degrees Celsius. "
    "Give me all three values in imperial/Fahrenheit units, each rounded to 1 decimal place."
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

    # Expected (before rounding): 27.6 lb, 211.3 miles, 87.8 F
