# Your workspace — Chapter 4

Write your Track 1 drills here. The folder is wired into the quality gate, so your code is
held to the same bar as the reference code:

```powershell
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest 04_sessions_state -q
```

`shared` is an installed package, so `from shared.models import make_model` works from any
file in here with no path juggling.

## Suggested files

```
exercises/
  stopwatch.py            Exercise 1
  trivia.py               Exercise 2
  notes.md                Exercise 3 — the three written answers
  thermostat.py           Exercise 4
  inspect_session.py      Exercise 5  (+ test_inspect_session.py)
  library_desk.py         Exercise 6  <- blank file, mandatory
  interview.py            Exercise 7
```

## Before you start

Two habits that will save you an hour each:

**1. Pace your loops.** The free tier allows ~15 requests per minute. A drill that fires
four turns back to back is fifteen requests in twenty seconds. Put
`await asyncio.sleep(8)` between turns.

**2. Print the session.** When an agent "forgets", look before you theorise:

```python
import json
print(json.dumps(await session.get_items(), indent=2))
```

Nine times out of ten the answer is visible immediately — an empty session (wrong
`db_path`), a session with someone else's turns in it (wrong `session_id`), or a session
that is perfectly correct and a prompt that is not.

## Do not

- Use expenses. That is the spine's domain, and reusing it defeats the point of drills.
- Copy from `with_sdk/` for Exercises 6 and 7. They are blank-file exercises; opening the
  reference turns them into typing practice.
