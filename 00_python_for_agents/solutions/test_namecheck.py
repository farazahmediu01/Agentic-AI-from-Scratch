"""
Tests for the Chapter 0 project - and your first pytest file.

    uv run pytest 00_python_for_agents/ -v

No API key. No network. Under two seconds. Every test here is a question you can
answer without a language model, and that is deliberate: **push every assertion
you can down to the cheap layer.** It is the rule the whole curriculum runs on.

HOW A TEST WORKS, IN THREE FACTS
---------------------------------
1. pytest collects files named `test_*.py` and functions named `test_*`.
2. A test passes if it finishes. It fails if an `assert` is False or it raises.
3. That is genuinely all. There is no framework to learn before you start.

TESTING ASYNC CODE WITHOUT A PLUGIN
-----------------------------------
`pytest` cannot await a coroutine on its own, and there are plugins that teach
it how. You do not need one: the test itself is an ordinary function, and it can
call `asyncio.run()` exactly the way `__main__` does.

    def test_something():
        result = asyncio.run(some_async_function())

One less dependency, and it keeps `asyncio.run` visible instead of hiding it
behind a decorator you have not met yet.
"""

from __future__ import annotations

import asyncio

import pytest
from pydantic import ValidationError

from namecheck import CHECKS, CheckResult, NameRequest, Report, domain, handle, run_checks

# =============================================================================
# The decorator did its job
# =============================================================================


def test_every_check_is_registered() -> None:
    """`@check` should have put all three functions in the registry."""
    assert set(CHECKS) == {"domain", "handle", "trademark"}


def test_check_returns_the_function_unchanged() -> None:
    """
    `@check` registers and returns the original function.

    Worth asserting: a decorator that accidentally returns None turns your
    function into None, and the error you get later is baffling.
    """
    assert CHECKS["domain"] is domain


# =============================================================================
# Validation happens before any work
# =============================================================================


def test_a_good_name_is_accepted() -> None:
    assert NameRequest(name="spendly").name == "spendly"


@pytest.mark.parametrize(
    "bad_name",
    [
        "a",  # too short
        "My App",  # capitals and a space
        "hello!",  # punctuation
        "x" * 31,  # too long
        "",  # empty
    ],
)
def test_bad_names_are_rejected(bad_name: str) -> None:
    """
    `parametrize` runs this test once per value - five tests from one function.

    Read the failure output when one breaks: pytest tells you which parameter
    it was, so a list of cases stays as debuggable as five separate tests.
    """
    with pytest.raises(ValidationError):
        NameRequest(name=bad_name)


# =============================================================================
# The checks themselves
# =============================================================================


def test_a_taken_domain_is_reported_unavailable() -> None:
    result = asyncio.run(domain("stripe"))
    assert isinstance(result, CheckResult)
    assert result.available is False
    assert "taken" in result.detail


def test_a_free_domain_is_reported_available() -> None:
    result = asyncio.run(domain("spendly"))
    assert result.available is True


def test_short_handles_are_taken() -> None:
    assert asyncio.run(handle("abc")).available is False
    assert asyncio.run(handle("spendly")).available is True


# =============================================================================
# The report object
# =============================================================================


def test_all_clear_is_true_only_when_everything_passed() -> None:
    good = Report(name="x", results=[CheckResult("domain", True, "")])
    mixed = Report(
        name="x",
        results=[CheckResult("domain", True, ""), CheckResult("handle", False, "")],
    )
    assert good.all_clear is True
    assert mixed.all_clear is False


def test_all_clear_is_false_when_nothing_ran() -> None:
    """
    An empty report must not claim success.

    `all([])` is True in Python - an easy way to ship a function that reports
    everything is fine because nothing was checked. This is the kind of bug a
    test finds and a read-through does not.
    """
    assert Report(name="x").all_clear is False


def test_blockers_names_only_the_failures() -> None:
    report = Report(
        name="x",
        results=[
            CheckResult("domain", True, ""),
            CheckResult("handle", False, ""),
            CheckResult("trademark", False, ""),
        ],
    )
    assert report.blockers == ["handle", "trademark"]


# =============================================================================
# The point of the whole chapter: concurrency is measurably faster
# =============================================================================


def test_concurrent_is_faster_than_sequential() -> None:
    """
    The async lesson, as an executable claim.

    The checks wait 0.4 + 0.6 + 0.5 = 1.5s in total, and the slowest single one
    is 0.6s. Run together, the whole thing should land near 0.6s; run in
    sequence, near 1.5s.

    The bounds are loose on purpose. A test that asserts `< 0.61` will fail on a
    loaded laptop and teach the student to distrust the suite - and a flaky test
    is worse than no test.
    """
    concurrent = asyncio.run(run_checks("spendly", concurrent=True))
    sequential = asyncio.run(run_checks("spendly", concurrent=False))

    assert concurrent.total_seconds < 1.0
    assert sequential.total_seconds > 1.2
    assert concurrent.total_seconds < sequential.total_seconds


def test_every_check_runs_in_both_modes() -> None:
    """Concurrency must not change the ANSWER, only the elapsed time."""
    concurrent = asyncio.run(run_checks("spendly", concurrent=True))
    sequential = asyncio.run(run_checks("spendly", concurrent=False))

    assert len(concurrent.results) == len(CHECKS)
    assert {r.service for r in concurrent.results} == {r.service for r in sequential.results}
    assert concurrent.all_clear == sequential.all_clear
