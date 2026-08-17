# Chapter 0 Project — Name Check

> **All six concepts, in one small program you'd actually use.**
>
> Time: **1.5 hrs** core, 2 hrs with the extensions.

## The problem

You have a name for a product. Before committing, you want to know three things:

```
is the domain free?      is the handle free?      is the trademark clear?
```

Three independent questions, each answered by a different slow service. **Nothing about question two depends on the answer to question one** — which makes this a concurrency problem rather than a sequence.

That is not a coincidence. It's the same shape as an agent calling three tools at once, which is why this is the project rather than a to-do list.

## What you're building

`exercises/namecheck.py`, run like this:

```powershell
uv run python 00_python_for_agents/exercises/namecheck.py spendly
uv run python 00_python_for_agents/exercises/namecheck.py spendly --slow
```

```
  spendly
    OK   domain     spendly.com is available     0.41s
    OK   handle     @spendly is available        0.60s
    OK   trademark  no conflict found            0.49s

  All clear. Total 0.60s
  mode: concurrent   sum of waits: 1.50s   slowest single wait: 0.60s
```

`--slow` runs the same checks sequentially. **That flag is the whole point** — same functions, same arguments, and the totals differ by 2.5×.

## Where each concept lands

| Concept | In this project |
|---|---|
| **typing** | `CheckFn`, `dict[str, CheckFn]`, `Report \| None` |
| **decorator** | `@check` registers a function into `CHECKS` |
| **dataclass** | `CheckResult` and `Report`, with `@property` for `all_clear` |
| **pydantic** | `NameRequest` validates the name *before* any work starts |
| **async** | every check is a coroutine; `gather` runs them together |
| **pytest** | `test_namecheck.py`, free and offline |

## Build it in this order

Each step runs on its own — don't write the whole file before running anything.

**1. The result objects.** `CheckResult` (service, available, detail, seconds) and `Report` (name, results, total_seconds) with an `all_clear` property.

> Careful with `all_clear`. `all([])` is `True` in Python, so the obvious one-liner reports success when nothing ran. There's a test for this.

**2. The validator.** `NameRequest` with a `name` field: 2–30 chars, pattern `^[a-z0-9-]+$`.

> Validate *first*. Without it, a name with a space sails through, fires three network calls, and fails deep inside the third. **Reject at the door and nothing half-runs.**

**3. The registry decorator.** `CHECKS: dict[str, CheckFn]` and a `@check` that registers and returns the function unchanged. Four lines.

**4. Three async checks.** `domain`, `handle`, `trademark`. Use `await asyncio.sleep(0.4 / 0.6 / 0.5)` to stand in for the network — that's not a cheat, a sleep and an HTTP call look identical to the event loop. Make each return a `CheckResult` with its own elapsed time.

Rules for "available" (arbitrary, so your tests are deterministic):

- `domain` — taken if the name is `google`, `stripe` or `notion`
- `handle` — taken if the name is 6 characters or fewer
- `trademark` — conflict if it starts with `apple` or ends with `book`

**5. The runner.** `run_checks(name, *, concurrent=True)`, with both branches visible:

```python
if concurrent:
    results = await asyncio.gather(*(fn(name) for fn in CHECKS.values()))
else:
    results = [await fn(name) for fn in CHECKS.values()]
```

Put them side by side deliberately. They call the same functions with the same arguments and differ only in **when they wait**, which turns out to be the only thing that matters.

**6. The CLI.** `argparse`, a `--slow` flag, and `asyncio.run(main())` at the bottom — exactly one, at the very edge of the program.

**7. The tests.** At least eight in `test_namecheck.py`.

## Acceptance checklist

### It works

- [ ] `namecheck.py spendly` prints three results and a total
- [ ] concurrent total lands near the **slowest** check (~0.6s), not the sum
- [ ] `--slow` lands near the **sum** (~1.5s)
- [ ] `namecheck.py "My App!"` is rejected with a readable message and **exits 1**
- [ ] the rejected name fires **zero** checks — prove it with a print inside one

### It uses the six

- [ ] `CheckFn` is a named type alias, not repeated inline
- [ ] `@check` returns the function unchanged, and there's a test asserting that
- [ ] `Report.all_clear` is a `@property`, and returns `False` for an empty report
- [ ] `NameRequest` rejects capitals, spaces, punctuation, too-short and too-long
- [ ] exactly one `asyncio.run()` in the whole file
- [ ] no `time.sleep` anywhere inside an `async def`

### It's proven

- [ ] `uv run pytest 00_python_for_agents/` — 8+ tests, under 2 seconds, no network
- [ ] one test asserts concurrent is measurably faster than sequential
- [ ] one test uses `pytest.raises`
- [ ] one test uses `parametrize`

### The gate

- [ ] `ruff format` · `ruff check` · `pyright` (0 errors, 0 warnings) · `pytest`

## Rubric

| Grade | What it looks like |
|---|---|
| **Not yet** | Checks run sequentially despite being `async`. Validation happens after the work. Mutable default on `Report.results`. |
| **Pass** | Both modes work with the expected timings, six concepts present, 8 tests green, gate clean. |
| **Strong** | The timing test has honest bounds (not `< 0.61`). `all_clear` handles the empty case. You can explain why `CheckFn` uses `Coroutine` rather than `Awaitable`. |
| **Distinction** | You added a check that can *fail* rather than return, handled it in `gather`, and can argue for or against `return_exceptions=True` in an agent context. |

---

## ⚡ Extensions `[depth]`

**A. Make one check fail.** Have `trademark` raise on a name containing `"xx"`. Run it — what does `gather` do to the other two? Now try `return_exceptions=True`. Which behaviour do you want when an agent is calling five tools and one dies?

**B. Add a timeout.** Wrap each check in `asyncio.wait_for(fn(name), timeout=0.5)`. One check now always times out. Report it as a third state — not available, not unavailable, but *unknown*.

> B is worth doing. "The tool didn't answer" is a real outcome that most people's first design has no shape for — and it's the same lesson Chapter 3 teaches about output models that force a value the agent doesn't have.

---

## Where next

**Chapter 1 — The Agent Loop.** You just built a registry of functions, dispatched into it by name, ran them concurrently, and returned a typed report.

Chapter 1 does the same thing with one change: **a language model decides which entries to call, and with what arguments.** That's the whole difference between a program and an agent.
