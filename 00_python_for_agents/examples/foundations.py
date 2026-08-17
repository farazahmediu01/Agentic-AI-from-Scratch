"""
Type hints and dataclasses - the two things Chapter 1's first file assumes.

    uv run python 00_python_for_agents/examples/foundations.py
    uv run pyright 00_python_for_agents/examples/foundations.py

Run BOTH commands. The second is the point: most of what type hints buy you never
shows up when you run the program. It shows up when you don't have to.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

# =============================================================================
# 1. Hints that describe SHAPE, not just type
# =============================================================================
#
# `list` tells you almost nothing. `list[Message]` tells you what is inside, and
# that is the difference between a hint that documents and a hint that catches
# bugs.

Message = dict[str, str]

# This is the actual shape of an agent's memory. You will build it in Chapter 1.
conversation: list[Message] = [
    {"role": "system", "content": "You are a helpful assistant."},
    {"role": "user", "content": "What is 15 times 7?"},
]


# =============================================================================
# 2. `X | None` - the single most valuable hint you will ever write
# =============================================================================
#
# "NoneType has no attribute ..." is the most common runtime error in Python.
# It happens because a function returned None on some path nobody thought about.


def find_user_message(messages: list[Message]) -> str | None:
    """
    Return the first user message, or None if there isn't one.

    The `| None` is a promise to the caller: **you must handle the empty case.**
    pyright will not let them forget.
    """
    for message in messages:
        if message["role"] == "user":
            return message["content"]
    return None


def demo_optional() -> None:
    found = find_user_message(conversation)

    # Uncomment to see pyright refuse it BEFORE you run:
    #   print(found.upper())
    #   -> "upper" is not a known attribute of "None"
    #
    # It is right. `find_user_message` can return None, and this line would
    # crash on any conversation with no user message. Narrowing fixes it:
    if found is not None:
        print(f"  first user message: {found.upper()}")
    else:
        print("  no user message found")


# =============================================================================
# 3. `Callable` - a type for functions themselves
# =============================================================================
#
# This is the hint that makes Chapter 1's tool registry possible. A dict whose
# VALUES are functions is the core data structure of every agent framework
# there is.


def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b


def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b


# Read it aloud: "a dict from string to (a function taking any arguments and
# returning a float)". In Chapter 1 this is called TOOL_REGISTRY.
#
# WHY `...` AND NOT `[float, float]`?
# `Callable[[float, float], float]` is more precise and it would be wrong here.
# That form describes *positional* parameters with no names, so pyright cannot
# check a `**kwargs` call against it -- and calling by name is the entire point
# of a registry a model dispatches into. `...` means "any signature", which
# honestly reflects what a registry of differently-shaped tools is.
#
# You are giving up argument checking at this line. Chapter 2 buys it back, at
# the boundary, with Pydantic -- which is a better place for it anyway, because
# by then the arguments are arriving from a language model rather than from you.
REGISTRY: dict[str, Callable[..., float]] = {
    "add": add,
    "multiply": multiply,
}


def demo_registry() -> None:
    name = "multiply"  # imagine a language model chose this
    args = {"a": 15.0, "b": 7.0}  # ...and these

    function = REGISTRY[name]
    result = function(**args)  # `**` unpacks the dict into named arguments
    print(f"  {name}(**{args}) -> {result}")

    print("  Chapter 1's agent loop is four lines longer than this. That is not")
    print("  an exaggeration -- look at TOOL_REGISTRY when you get there.")


# =============================================================================
# 4. `cast()` - telling the checker something it cannot work out
# =============================================================================


def demo_cast() -> None:
    # Say a library hands you back `object` but you know from its docs that this
    # particular call always returns a string.
    raw: object = "gemini-2.5-flash"

    # print(raw.upper())          # pyright: "upper" is not a known attribute
    model_name = cast(str, raw)
    print(f"  cast to str -> {model_name.upper()}")

    print()
    print("  `cast` changes NOTHING at runtime. It is you telling the type checker")
    print("  'trust me here'. That makes it a promise, and promises can be wrong --")
    print("  so use it where a library's types are weaker than its guarantees, and")
    print("  never to silence an error you have not understood.")
    print()
    print("  Chapter 1 has exactly one, in `agent.py`, and it is commented.")


# =============================================================================
# 5. Dataclasses - a return value with more than one thing in it
# =============================================================================
#
# THE PROBLEM: a function that has several things to tell you.
#
#   return answer, tools_used, iterations, hit_limit
#
# Now every caller writes `a, b, c, d = run(...)`, in the right order, forever.
# Add a fifth and every call site breaks. Worse, `result[2]` tells the next
# reader nothing at all.


@dataclass
class RunReport:
    """
    What happened during one agent run.

    This is a simplified `AgentRun` -- the real one arrives in Chapter 1 and you
    will read it in every chapter after.
    """

    final_answer: str
    iterations: int = 0

    # MUTABLE DEFAULTS: the trap worth meeting once, deliberately.
    #
    #   tool_names: list[str] = []          <- WRONG, and Python will not stop you
    #
    # That list is created ONCE, when the class is defined, and every instance
    # then shares it. Appending to one report's list appends to all of them.
    # `default_factory` says "call this to make a fresh one per instance."
    tool_names: list[str] = field(default_factory=list)

    @property
    def used_tools(self) -> bool:
        """
        A value computed from other fields, read like a plain attribute.

        `report.used_tools` -- no parentheses. Use `@property` for things that
        are cheap and feel like facts about the object rather than actions.
        """
        return len(self.tool_names) > 0


def demo_dataclass() -> None:
    report = RunReport(final_answer="105", iterations=3, tool_names=["multiply"])

    print(f"  {report}")  # dataclasses print themselves readably, for free
    print(f"  report.used_tools -> {report.used_tools}")

    # And equality compares by value, also for free.
    same = RunReport(final_answer="105", iterations=3, tool_names=["multiply"])
    print(f"  two identical reports are equal -> {report == same}")

    print()
    print("  You wrote no __init__, no __repr__, no __eq__. That is the whole")
    print("  pitch: a dataclass is a class whose job is to hold named values.")


def main() -> None:
    for title, demo in (
        ("2. X | None and narrowing", demo_optional),
        ("3. Callable and a function registry", demo_registry),
        ("4. cast()", demo_cast),
        ("5. dataclasses", demo_dataclass),
    ):
        print("=" * 72)
        print(title)
        print()
        demo()
        print()


if __name__ == "__main__":
    main()
