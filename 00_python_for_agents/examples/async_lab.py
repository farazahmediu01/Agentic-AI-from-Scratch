"""
The async lab - six experiments, each one killing a specific misconception.

    uv run python 00_python_for_agents/examples/async_lab.py          # all six
    uv run python 00_python_for_agents/examples/async_lab.py 3        # just experiment 3

No API key. No network. Everything here is simulated with sleeps, which is not a
cheat -- `asyncio.sleep` is a genuinely accurate stand-in for "waiting on
something outside this program", and that is all a network call ever is.

HOW TO USE THIS FILE
--------------------
Run each experiment. **Predict the timing before you look.** Every experiment
prints how long it took, and the timings are the whole lesson -- async is one of
the few topics where the concept is directly measurable in seconds.

THE MENTAL MODEL: ONE PERSON, SEVERAL MACHINES
----------------------------------------------
You are doing laundry. You have one pair of hands.

    You load the washing machine and press start.   <- this takes you 5 seconds
    The machine now runs for 30 minutes.            <- this takes you NOTHING

The question that decides everything: **what do you do during those 30 minutes?**

    Synchronous you  : sits in front of the machine and watches it.
    Asynchronous you : goes and loads the dishwasher, then answers an email.

Both versions of you have exactly one pair of hands. You never do two things at
literally the same instant. The async version is not faster at any single task
-- it is faster overall because it stopped treating *waiting* as *working*.

Map it to the code and every keyword lands:

    async def wash():   this job has waiting in it
    await machine       "the machine is running now; I am free -- someone else go"
    asyncio.run(...)    the person. Somebody has to actually do the walking around
    asyncio.gather(...) start the washer AND the dishwasher before waiting on either

And the one that catches everyone:

    folding clothes     no waiting involved, only hands. Nothing to hand off.
                        This is CPU work, and async does nothing for it.
"""

from __future__ import annotations

import asyncio
import sys
import time

# -----------------------------------------------------------------------------
# A stand-in for "something outside this program that takes time".
# -----------------------------------------------------------------------------


async def check_domain(name: str) -> str:
    """Pretend to ask a DNS server whether a domain is free. Takes ~0.4s."""
    await asyncio.sleep(0.4)
    return f"{name}.com is available"


async def check_username(name: str) -> str:
    """Pretend to ask a social API whether a handle is free. Takes ~0.6s."""
    await asyncio.sleep(0.6)
    return f"@{name} is taken"


async def check_trademark(name: str) -> str:
    """Pretend to search a trademark registry. Takes ~0.5s."""
    await asyncio.sleep(0.5)
    return f"no trademark conflict for {name}"


# -----------------------------------------------------------------------------
# 1. Calling an async function does not run it.
#
# THE MISCONCEPTION: "I called it, so it ran."
# -----------------------------------------------------------------------------


def experiment_1() -> None:
    print("1. What does calling an async function actually give you?\n")

    result = check_domain("spendly")  # note: no await
    print(f"   check_domain('spendly')  ->  {result!r}")
    print(f"   type                     ->  {type(result).__name__}")

    # Without this, Python warns 'coroutine was never awaited' - a real warning
    # you will see for real, and now you know what it means.
    result.close()

    print()
    print("   You did not get a string. You got a COROUTINE OBJECT: a job that has")
    print("   been described and not started. Think of it as a written note saying")
    print("   'wash the towels' -- writing the note is not doing the laundry.")
    print()
    print("   `await` is what hands the note to someone who will actually do it.")


# -----------------------------------------------------------------------------
# 2. `await` in a row is still a queue.
#
# THE MISCONCEPTION - and this is the big one - "I made it async, so it's fast."
# -----------------------------------------------------------------------------


async def experiment_2() -> None:
    print("2. Three awaits, one after another\n")

    start = time.perf_counter()
    a = await check_domain("spendly")
    b = await check_username("spendly")
    c = await check_trademark("spendly")
    elapsed = time.perf_counter() - start

    for line in (a, b, c):
        print(f"   {line}")
    print(f"\n   elapsed: {elapsed:.2f}s   (0.4 + 0.6 + 0.5 = 1.5)")
    print()
    print("   Every function here is `async`. Every call is `await`ed. And it took")
    print("   exactly as long as doing them one at a time, because that is what we")
    print("   asked for: `await` means 'I need this answer before my next line'.")
    print()
    print("   **This is the single most common async mistake.** Marking things")
    print("   `async` buys you nothing on its own. You have loaded the washing")
    print("   machine and then stood there watching it, three times.")


# -----------------------------------------------------------------------------
# 3. gather() is where the win actually is.
# -----------------------------------------------------------------------------


async def experiment_3() -> None:
    print("3. The same three, started together\n")

    start = time.perf_counter()
    a, b, c = await asyncio.gather(
        check_domain("spendly"),
        check_username("spendly"),
        check_trademark("spendly"),
    )
    elapsed = time.perf_counter() - start

    for line in (a, b, c):
        print(f"   {line}")
    print(f"\n   elapsed: {elapsed:.2f}s   (the SLOWEST one, 0.6 - not the sum)")
    print()
    print("   Total time is now the longest single wait instead of the sum of all")
    print("   of them. You started all three machines, then waited once.")
    print()
    print("   Notice the results came back in the order you ASKED for them, not the")
    print("   order they finished in. gather() preserves your ordering, which is why")
    print("   unpacking `a, b, c` is safe.")


# -----------------------------------------------------------------------------
# 4. One blocking call freezes everything.
#
# This is the experiment that makes the event loop visible.
# -----------------------------------------------------------------------------


async def polite_waiter(label: str, seconds: float) -> str:
    """Waits the async way: hands control back while it waits."""
    await asyncio.sleep(seconds)
    return f"{label} done"


async def rude_waiter(label: str, seconds: float) -> str:
    """
    Waits the WRONG way inside async code.

    `time.sleep` does not hand control back. It sits on the one pair of hands and
    refuses to let go, so nothing else in the entire program can make progress.
    """
    time.sleep(seconds)
    return f"{label} done"


async def experiment_4() -> None:
    print("4. asyncio.sleep vs time.sleep, inside async code\n")

    start = time.perf_counter()
    await asyncio.gather(
        polite_waiter("polite-1", 0.5),
        polite_waiter("polite-2", 0.5),
        polite_waiter("polite-3", 0.5),
    )
    polite = time.perf_counter() - start

    start = time.perf_counter()
    await asyncio.gather(
        rude_waiter("rude-1", 0.5),
        rude_waiter("rude-2", 0.5),
        rude_waiter("rude-3", 0.5),
    )
    rude = time.perf_counter() - start

    print(f"   three polite_waiter (asyncio.sleep) : {polite:.2f}s")
    print(f"   three rude_waiter   (time.sleep)    : {rude:.2f}s")
    print()
    print("   Identical code. Identical gather(). Identical durations. One is 3x")
    print("   slower, and nothing about the shape of the program says why.")
    print()
    print("   `asyncio.sleep` says 'I'm waiting -- somebody else go'.")
    print("   `time.sleep`    says nothing and holds the hands.")
    print()
    print("   THE RULE: inside `async def`, every waiting call must be an async one.")
    print("   One ordinary blocking call anywhere -- `requests.get`, `time.sleep`, a")
    print("   heavy file read -- silently converts your concurrent program back into")
    print("   a sequential one. Nothing crashes. It just gets slow, and the reason")
    print("   is invisible unless you know to look for it.")


# -----------------------------------------------------------------------------
# 5. Async is not threads, and does not help CPU work.
# -----------------------------------------------------------------------------


async def count_to(n: int) -> int:
    """Pure CPU work. There is no waiting here to hand off."""
    total = 0
    for i in range(n):
        total += i * i
    return total


async def experiment_5() -> None:
    print("5. What async does NOT do\n")

    size = 3_000_000

    start = time.perf_counter()
    await count_to(size)
    await count_to(size)
    one_at_a_time = time.perf_counter() - start

    start = time.perf_counter()
    await asyncio.gather(count_to(size), count_to(size))
    gathered = time.perf_counter() - start

    print(f"   two counts, awaited in sequence : {one_at_a_time:.2f}s")
    print(f"   two counts, gathered            : {gathered:.2f}s")
    print()
    print("   Barely any difference -- and gather() may even be slightly slower.")
    print()
    print("   This is folding clothes. There is no machine running in the")
    print("   background; the work needs your hands the entire time. gather() can")
    print("   only interleave at `await` points, and pure computation has none.")
    print()
    print("   async is for WAITING, not for computing. If you need real parallel")
    print("   CPU work you want processes (`multiprocessing`), which is a different")
    print("   tool for a different problem.")


# -----------------------------------------------------------------------------
# 6. Why async 'spreads'.
# -----------------------------------------------------------------------------


def a_normal_function() -> str:
    """
    An ordinary function cannot `await`. Uncomment the line to see it fail.

    That is not a rule Python invented to annoy you: `await` means "pause me and
    let the loop run someone else", and an ordinary function has no way to be
    paused and resumed.
    """
    # return await check_domain("spendly")   # SyntaxError: 'await' outside async function
    return "ordinary functions cannot await"


async def experiment_6() -> None:
    print("6. Why async spreads through a codebase\n")

    print(f"   {a_normal_function()}")
    print()
    print("   To `await` something you must be inside `async def`. So the moment one")
    print("   function deep in your stack becomes async, every caller must become")
    print("   async too, all the way up -- until someone calls `asyncio.run()`.")
    print()
    print("   People call this 'function colouring', and it is the real cost of")
    print("   async. It is worth knowing BEFORE you meet it, because the fix is")
    print("   architectural, not local.")
    print()
    print("   Where you will meet this in Chapter 1:")
    print()
    print("       result = await Runner.run(agent, message)      # the SDK is async")
    print("       result = Runner.run_sync(agent, message)       # the escape hatch")
    print()
    print("   `run_sync` starts a loop, runs the coroutine, and hands you the result")
    print("   -- so ordinary code can call it. Use it while you are learning. Reach")
    print("   for the async version when you want two agents running at once.")


# -----------------------------------------------------------------------------


async def main() -> None:
    experiments = {
        1: experiment_1,
        2: experiment_2,
        3: experiment_3,
        4: experiment_4,
        5: experiment_5,
        6: experiment_6,
    }

    wanted = [int(a) for a in sys.argv[1:] if a.isdigit()] or list(experiments)

    for number in wanted:
        run = experiments.get(number)
        if run is None:
            continue
        print("=" * 72)
        outcome = run()
        if asyncio.iscoroutine(outcome):
            await outcome
        print()


if __name__ == "__main__":
    # THE ENTRY POINT. Somebody has to start the loop, and `asyncio.run` is that
    # somebody. It creates the loop, runs your coroutine until it finishes, and
    # closes the loop again. Exactly one of these per program, at the very edge.
    asyncio.run(main())
