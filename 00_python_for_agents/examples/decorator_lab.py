"""
Decorators - and specifically the one shape that runs this whole curriculum.

    uv run python 00_python_for_agents/examples/decorator_lab.py

You will meet `@tool`, `@function_tool`, `@dataclass`, `@property`,
`@input_guardrail` and `@function_tool(failure_error_function=...)` in this
course. All of them are the same idea. Learn it once here and none of them are
mysterious later.

THE ONE SENTENCE
----------------
A decorator is a function that takes a function and gives you something back.

    @shout
    def greet(): ...

is *literally* shorthand for:

    def greet(): ...
    greet = shout(greet)

That is the entire language feature. Everything else is what you choose to put
inside `shout`.
"""

from __future__ import annotations

import functools
import time
from collections.abc import Callable
from typing import Any

# =============================================================================
# 1. Prove the shorthand claim
# =============================================================================


def shout(fn: Callable[[], str]) -> Callable[[], str]:
    """Take a function, return a new one that upper-cases its result."""

    def wrapper() -> str:
        return fn().upper() + "!"

    return wrapper


def greet_plain() -> str:
    return "hello"


greet_manual = shout(greet_plain)  # the long way


@shout  # the short way -- identical
def greet_decorated() -> str:
    return "hello"


def demo_equivalence() -> None:
    print(f"  greet_plain()      -> {greet_plain()!r}")
    print(f"  greet_manual()     -> {greet_manual()!r}")
    print(f"  greet_decorated()  -> {greet_decorated()!r}")
    print()
    print("  The last two are the same thing written two ways. `@` is syntax, not")
    print("  magic -- it rebinds the name to whatever the decorator returned.")


# =============================================================================
# 2. A decorator that does something useful: timing
# =============================================================================


def timed(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Print how long a function took.

    `*args, **kwargs` is how a wrapper accepts ANY arguments and passes them
    straight through. It is what lets one decorator work on every function you
    own, whatever their signatures.
    """

    @functools.wraps(fn)  # see below -- this line matters more than it looks
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        start = time.perf_counter()
        result = fn(*args, **kwargs)
        elapsed = time.perf_counter() - start
        print(f"    [{fn.__name__} took {elapsed * 1000:.1f}ms]")
        return result

    return wrapper


@timed
def slow_square(n: int) -> int:
    """Square a number, slowly, for demonstration purposes."""
    scratch = 0
    for i in range(n * 100_000):
        scratch = (scratch + i) % 1_000_003
    return n * n


def demo_timed() -> None:
    print(f"  slow_square(5) -> {slow_square(5)}")
    print()
    print("  Nothing inside slow_square changed. That is the appeal: you add a")
    print("  behaviour to a function without editing the function.")


# =============================================================================
# 3. `functools.wraps` - the bug you would otherwise ship
# =============================================================================


def forgetful(fn: Callable[..., Any]) -> Callable[..., Any]:
    """A decorator that loses the identity of what it wraps."""

    def wrapper(*args: Any, **kwargs: Any) -> Any:
        return fn(*args, **kwargs)

    return wrapper


@forgetful
def documented_tool(city: str) -> str:
    """Look up the weather for a city."""
    return f"sunny in {city}"


def demo_wraps() -> None:
    print(f"  documented_tool.__name__ -> {documented_tool.__name__!r}")
    print(f"  documented_tool.__doc__  -> {documented_tool.__doc__!r}")
    print()
    print("  The name and the docstring are GONE -- replaced by the wrapper's.")
    print()
    print("  Now hold that next to how tools work in this course: `@function_tool`")
    print("  reads your docstring and sends it to the model as the tool's")
    print("  description. A decorator that forgets the docstring produces a tool")
    print("  the model cannot understand, and nothing crashes -- the agent just")
    print("  quietly gets worse at choosing it.")
    print()
    print("  `@functools.wraps(fn)` copies the name, docstring and annotations")
    print("  across. Compare `slow_square` above, which used it:")
    print(f"    slow_square.__name__ -> {slow_square.__name__!r}")
    print(f"    slow_square.__doc__  -> {slow_square.__doc__!r}")


# =============================================================================
# 4. The registry decorator - the shape this whole curriculum is built on
# =============================================================================

TOOLS: dict[str, Callable[..., Any]] = {}


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Register a function as a tool, and hand it back untouched.

    Note what this does NOT do: it does not wrap, change or slow the function
    down. `@tool` here is pure side effect -- it puts an entry in a dict. The
    function you get back is the one you wrote.

    That is a completely legitimate decorator, and it is 80% of what `@tool` in
    Chapter 2 does. The other 20% is reading the signature to build a schema.
    """
    TOOLS[fn.__name__] = fn
    return fn


@tool
def word_count(text: str) -> int:
    """Count the words in a piece of text."""
    return len(text.split())


@tool
def slugify(title: str) -> str:
    """Turn a title into a url-safe slug."""
    return "-".join(title.lower().split())


@tool
def password_strength(password: str) -> str:
    """Rate a password as weak, ok or strong."""
    score = sum(
        [
            len(password) >= 12,
            any(c.isdigit() for c in password),
            any(c.isupper() for c in password),
            any(not c.isalnum() for c in password),
        ]
    )
    return ("weak", "weak", "ok", "strong", "strong")[score]


def demo_registry() -> None:
    print(f"  registered tools: {list(TOOLS)}")
    print()

    # This is dispatch-by-name, and it is exactly what an agent does with the
    # tool name a model gives it.
    for name, argument in (
        ("word_count", "the quick brown fox jumps"),
        ("slugify", "Build An Agent From Scratch"),
        ("password_strength", "correct-horse-9B"),
    ):
        print(f"  {name}({argument!r}) -> {TOOLS[name](argument)!r}")

    print()
    print("  You just built a tool registry in nine lines. Chapter 1 builds this")
    print("  by hand and Chapter 2 replaces it with a decorator that also")
    print("  generates the JSON schema. You now know what the `@` is doing.")


def main() -> None:
    for title, demo in (
        ("1. @ is shorthand, and nothing else", demo_equivalence),
        ("2. A decorator that adds behaviour", demo_timed),
        ("3. functools.wraps, and the bug without it", demo_wraps),
        ("4. The registry decorator", demo_registry),
    ):
        print("=" * 72)
        print(title)
        print()
        demo()
        print()


if __name__ == "__main__":
    main()
