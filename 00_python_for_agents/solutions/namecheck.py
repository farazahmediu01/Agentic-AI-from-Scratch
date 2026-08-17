"""
Name Check - the Chapter 0 project, and all six concepts in one small program.

    uv run python 00_python_for_agents/solutions/namecheck.py spendly
    uv run python 00_python_for_agents/solutions/namecheck.py spendly --slow

THE PROBLEM
-----------
You have a name for a product. Before committing you want to know three things:

    is the domain free?      is the handle free?      is the trademark clear?

Three independent questions, each answered by a different slow service. Nothing
about question two depends on the answer to question one, which makes this a
concurrency problem rather than a sequence -- and that is exactly the shape of an
agent calling three tools at once.

WHERE EACH CHAPTER 0 CONCEPT SHOWS UP
--------------------------------------
    typing      CheckFn, dict[str, CheckFn], `X | None`
    decorator   @check registers a function into CHECKS
    dataclass   CheckResult and Report, with a @property
    pydantic    NameRequest validates the input before any work starts
    async       every check is a coroutine; gather runs them together
    pytest      test_namecheck.py, free and offline

Read this next to `01_agent_loop/from_scratch/agent.py` when you get there. The
registry, the dispatch and the report object are the same three ideas. All that
chapter adds is a language model choosing which entries to call.
"""

from __future__ import annotations

import argparse
import asyncio
import time
from collections.abc import Callable, Coroutine
from dataclasses import dataclass, field
from typing import Any

from pydantic import BaseModel, Field, ValidationError

# =============================================================================
# TYPING - name the shape of a check once, use it everywhere
# =============================================================================
#
# "a function that takes a str and returns a coroutine producing a CheckResult".
# Spelling it out once means the registry, the decorator and the runner all agree.
#
# WHY `Coroutine` AND NOT THE SIMPLER `Awaitable`?
# Every coroutine is awaitable, so `Awaitable[CheckResult]` reads better and is
# what most people write first. It also does not type-check: `asyncio.run()`
# specifically requires a *coroutine*, because it has to drive the thing to
# completion, and plenty of awaitables (a Future, an object with __await__)
# cannot be driven that way. pyright is right to object, and the fix is to say
# what you actually have.
#
# The three `Any`s are the send and yield types of the coroutine protocol. You
# will never use them. `Coroutine[Any, Any, T]` is idiomatically just "a coroutine
# returning T".
CheckFn = Callable[[str], Coroutine[Any, Any, "CheckResult"]]

CHECKS: dict[str, CheckFn] = {}


# =============================================================================
# DATACLASSES - the two result objects
# =============================================================================


@dataclass
class CheckResult:
    """The outcome of one check."""

    service: str
    available: bool
    detail: str
    seconds: float = 0.0


@dataclass
class Report:
    """Everything the run produced, in one object."""

    name: str
    results: list[CheckResult] = field(default_factory=list)
    total_seconds: float = 0.0

    @property
    def all_clear(self) -> bool:
        """True only when every check came back available."""
        return bool(self.results) and all(r.available for r in self.results)

    @property
    def blockers(self) -> list[str]:
        """The services that said no. Empty when all_clear is True."""
        return [r.service for r in self.results if not r.available]


# =============================================================================
# PYDANTIC - validate the request before doing any slow work
# =============================================================================


class NameRequest(BaseModel):
    """
    What we are allowed to check.

    Validating first matters more than it looks: without this, a name with a
    space in it would sail through, fire three network calls, and fail somewhere
    deep inside the third one. **Reject at the door and nothing half-runs.**
    """

    name: str = Field(
        min_length=2,
        max_length=30,
        pattern=r"^[a-z0-9-]+$",
        description="Lowercase letters, digits and hyphens only.",
    )


# =============================================================================
# DECORATOR - registration, in four lines
# =============================================================================


def check(fn: CheckFn) -> CheckFn:
    """Register a check under its own function name, and return it unchanged."""
    CHECKS[fn.__name__] = fn
    return fn


# =============================================================================
# ASYNC - three checks, each mostly spent waiting
# =============================================================================
#
# `asyncio.sleep` stands in for a network call. That is not a simplification --
# from the event loop's point of view a sleep and an HTTP request are the same
# thing: a period during which this coroutine has nothing to do and something
# else should run.


async def _pretend_network(seconds: float) -> None:
    await asyncio.sleep(seconds)


@check
async def domain(name: str) -> CheckResult:
    """Is <name>.com registered?"""
    start = time.perf_counter()
    await _pretend_network(0.4)
    taken = name in {"google", "stripe", "notion"}
    return CheckResult(
        service="domain",
        available=not taken,
        detail=f"{name}.com is {'taken' if taken else 'available'}",
        seconds=time.perf_counter() - start,
    )


@check
async def handle(name: str) -> CheckResult:
    """Is @<name> free on the usual social platforms?"""
    start = time.perf_counter()
    await _pretend_network(0.6)
    taken = len(name) <= 6  # short handles are always gone
    return CheckResult(
        service="handle",
        available=not taken,
        detail=f"@{name} is {'taken' if taken else 'available'}",
        seconds=time.perf_counter() - start,
    )


@check
async def trademark(name: str) -> CheckResult:
    """Does the name collide with a registered trademark?"""
    start = time.perf_counter()
    await _pretend_network(0.5)
    conflict = name.startswith("apple") or name.endswith("book")
    return CheckResult(
        service="trademark",
        available=not conflict,
        detail=("possible conflict" if conflict else "no conflict found"),
        seconds=time.perf_counter() - start,
    )


# =============================================================================
# THE RUNNER - sequential and concurrent, so the difference is measurable
# =============================================================================


async def run_checks(name: str, *, concurrent: bool = True) -> Report:
    """
    Run every registered check against `name`.

    Compare the two branches. They call the same functions with the same
    arguments and differ only in WHEN they wait -- which turns out to be the
    only thing that matters.
    """
    start = time.perf_counter()

    if concurrent:
        # Build every coroutine first, hand them all to the loop, wait once.
        results = await asyncio.gather(*(fn(name) for fn in CHECKS.values()))
    else:
        # Wait for each one to finish before starting the next.
        results = [await fn(name) for fn in CHECKS.values()]

    return Report(
        name=name,
        results=list(results),
        total_seconds=time.perf_counter() - start,
    )


def parse_request(raw_name: str) -> NameRequest | None:
    """Validate, or explain why not. Returns None when the name is unusable."""
    try:
        return NameRequest(name=raw_name)
    except ValidationError as exc:
        for error in exc.errors():
            print(f"  rejected: {error['msg']}  (you sent: {error.get('input')!r})")
        return None


def print_report(report: Report) -> None:
    print(f"\n  {report.name}")
    for result in report.results:
        mark = "OK  " if result.available else "NO  "
        print(f"    {mark} {result.service:<10} {result.detail:<28} {result.seconds:.2f}s")

    print()
    if report.all_clear:
        print(f"  All clear. Total {report.total_seconds:.2f}s")
    else:
        print(f"  Blocked by: {', '.join(report.blockers)}. Total {report.total_seconds:.2f}s")


async def main() -> None:
    parser = argparse.ArgumentParser(description="Check whether a product name is free.")
    parser.add_argument("name", help="the name to check, lowercase")
    parser.add_argument(
        "--slow",
        action="store_true",
        help="run the checks one after another, to see what concurrency buys",
    )
    args = parser.parse_args()

    request = parse_request(args.name)
    if request is None:
        raise SystemExit(1)

    report = await run_checks(request.name, concurrent=not args.slow)
    print_report(report)

    mode = "sequential" if args.slow else "concurrent"
    slowest = max((r.seconds for r in report.results), default=0.0)
    total = sum(r.seconds for r in report.results)
    print(f"  mode: {mode}   sum of waits: {total:.2f}s   slowest single wait: {slowest:.2f}s")
    print()
    print("  Run it both ways. Concurrent lands near the SLOWEST check; sequential")
    print("  lands near the SUM. Same functions, same arguments -- the only")
    print("  difference is whether you waited once or three times.")


if __name__ == "__main__":
    asyncio.run(main())
