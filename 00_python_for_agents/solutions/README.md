# Chapter 0 — reference solution

**Open after you attempt, not before.**

| File | What it is |
|---|---|
| `namecheck.py` | The chapter project — all six concepts in one program |
| `test_namecheck.py` | Its proof layer, and your first pytest file to read |

```powershell
uv run python 00_python_for_agents/solutions/namecheck.py spendly
uv run python 00_python_for_agents/solutions/namecheck.py spendly --slow
uv run pytest 00_python_for_agents/ -v
```

## Two decisions worth reading the comments for

**`CheckFn` uses `Coroutine`, not `Awaitable`.** Every coroutine is awaitable, so `Awaitable[CheckResult]` reads better and is what most people write first. It also doesn't type-check: `asyncio.run()` specifically requires a *coroutine*, because it has to drive the thing to completion, and plenty of awaitables can't be driven that way. pyright is right to object.

**`Report.all_clear` guards the empty case.** `all([])` is `True` in Python, so the obvious one-liner reports success when nothing ran. There's a test for it, and it's the kind of bug a test finds and a read-through doesn't.

## What this is a rehearsal for

Read `namecheck.py` next to `01_agent_loop/from_scratch/agent.py` once you get there:

| Here | Chapter 1 |
|---|---|
| `CHECKS: dict[str, CheckFn]` | `TOOL_REGISTRY: dict[str, Callable]` |
| `@check` | `@tool` (Chapter 2) |
| `CHECKS[name](arg)` | `TOOL_REGISTRY[name](**args)` |
| `Report` | `AgentRun` |
| you chose which checks to run | **a language model chooses** |

That last row is the entire difference between a program and an agent.
