# Chapter 4 — reference solutions

**Read these after you attempt the work, not before.** They exist for grading and
self-checking. Opening `expense_agent_v4.py` before writing your own turns §10 and
Exercise 6 into typing practice.

## The files

| File | What it is for |
|---|---|
| `_bootstrap.py` | Runtime `sys.path` shim. Chapter 3 explains why it must exist |
| `spendly_context.py` | The `User` context object, and the two users M5 needs |
| `expense_agent_v4.py` | The spine: Chapter 3's agent plus `session=` and `context=` |
| `check_multiturn.py` | Five multi-turn cases — the questions one turn cannot ask |
| `check_regression.py` | Chapter 3's nine cases, run against **v4** |
| `test_context.py` | Thirteen offline tests. No API key, ~1 second |
| `RUNS.md` | Evidence: model, date, actual output |

## Run them

```powershell
uv run pytest 04_sessions_state -q                                # free
uv run python 04_sessions_state/solutions/expense_agent_v4.py     # the 2-turn demo
uv run python 04_sessions_state/solutions/check_multiturn.py      # ~11 min
uv run python 04_sessions_state/solutions/check_regression.py     # ~15 min
```

Both harnesses take `--only 1,4` to re-check a subset after a rate-limited run. Use it —
it is the difference between spending 8 requests and 80.

## The four things worth reading for their own sake

**1. `_run_with_backoff` in `expense_agent_v4.py`** — why a quota failure arrives as
`MaxTurnsExceeded` rather than `RateLimitError`, and why a retry inside a session is not a
clean retry.

**2. `MultiTurnRun` in `check_multiturn.py`** — Chapter 3's `RunLike` Protocol *widened by
inheritance* rather than edited. Three options were available and only one leaves the
shipped chapter alone.

**3. `run_case` in `check_multiturn.py`** — carries the bug it shipped first, in its
docstring. The session was cleared per **turn** instead of per **case**, which wiped turn 1
before turn 2 ran. It scored 2/9 and looked exactly like a broken agent.

**4. The comment above `budgets` in `spendly_context.py`** — why `default_factory` and why
`dict(...)`. Two separate bugs, one line.

## If a case fails

Diagnose the **shape** before you touch the agent:

| Shape | Cause | Do |
|---|---|---|
| `branch=none turns=0`, a `waiting` line above | Free-tier quota in costume | Switch `MODEL_NAME`, or wait, then `--only` |
| A real branch, some checks FAIL | Genuine defect | Read the check label — it names the field and the value |
| Passes on re-run | Non-determinism | Run 3× before changing anything |

**Never weaken a check to make a run pass.** If a check is wrong, it is wrong because it
asserts the wrong *thing* — fix what it asserts, not the threshold. Case M3 shipped with
`session_items <= 2`, which was a proxy for "the other conversation did not leak in" and a
bad one. The fix was to assert the actual claim, not to raise the number.
