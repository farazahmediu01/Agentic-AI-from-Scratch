# Chapter 4 — Project

Two tracks, both mandatory. **Core 120 min · Full 210 min** — the sum of the
estimates below, and the figure the README's budget table carries.

| Part | Tier | Min |
|---|---|-----|
| Track 2 — Spendly Lite v4 | `[core]` | 60 |
| Track 3 — your own agent's Ch4 increment | `[core]` | 60 |
| Challenges 1–3 | `[depth]` | 90 |

Dataset wall-clock (~26 min of waiting) is not counted — start the runs and read
the README while they go.

| Track | What | Domain | Graded on |
|---|---|---|---|
| 2️⃣ **The Spine** | Spendly Lite v4 — multi-turn | Expenses, always | The golden datasets, **plus every prior chapter's cases still passing** |
| 3️⃣ **Your Own Agent** | Chapter 4's capability in *your* agent | Whatever you chose in Ch1 | **Evidence, not functionality** |

---

# Track 2 — Spendly Lite v4 `[core]` · 60 min

## The requirement

Spendly can now hold a conversation, and knows who it is holding it with.

```
TURN 1   "Log 500 at Metro."
         -> need_more_info, missing=['category']

TURN 2   "Groceries."
         -> logged: Metro, 500, Groceries
```

Chapter 3 could produce turn 1's question. Nothing in Chapter 3 could hear turn 2's
answer. That is the entire delta.

## What you build

| File | What |
|---|---|
| `spendly_context.py` | A `User` dataclass: id, name, timezone, monthly income, **per-user budgets** |
| `expense_agent_v4.py` | v3 + `session=` + `context=` + one context-aware tool |
| `check_multiturn.py` | Five multi-turn cases |
| `check_regression.py` | Chapter 3's nine cases, run against **v4** |
| `test_context.py` | Offline tests — no API key, ~1 second |
| `RUNS.md` | Evidence: model, date, real output |

### The change that is smaller than you expect

```python
result = await Runner.run(agent, prompt, session=session, context=user)
```

Chapter 3's `replies.py` is imported unchanged. Chapter 2's tools and storage are imported
unchanged. **If adding memory to an agent had required rewriting its tools, the memory was
in the wrong place.**

### The one tool that changed

```python
@function_tool
def get_budget(ctx: RunContextWrapper[User], category: Category) -> float:
    return ctx.context.budget_for(category)
```

Since Chapter 1, `MONTHLY_BUDGETS` has been a module-level dict — which quietly asserted
that every Spendly user has the same budget. True only because there was one user, and
they were hard-coded.

**What did not move: the ledger.** Expenses still live in `expense_store`, shared.

> A **context** holds what your app knows about *this run*. A **store** holds what your app
> knows, *period*. A budget is configuration attached to a person; an expense is a fact
> about the world.

Making the ledger genuinely per-user is a real change with a real seam. It is Challenge 2
below, and leaving it undone is how you get to see where the seam goes.

---

## The golden datasets

```powershell
uv run pytest 04_sessions_state -q                                # free, ~1s
uv run python 04_sessions_state/solutions/check_multiturn.py      # ~11 min
uv run python 04_sessions_state/solutions/check_regression.py     # ~15 min
```

| Case | Asks |
|---|---|
| **M1** | Does turn 2 complete an action from turn 1's values? |
| **M2** | **The control** — with no session, does it fail to? |
| **M3** | Does one `session_id` stay out of another's conversation? |
| **M4** | The ledger changed between turns. Does it re-read, or recite? |
| **M5** | One prompt, two users — two different correct numbers? |

**M2 is not padding.** An eval with no control cannot distinguish *"the session works"*
from *"the model guessed well"* — and this chapter's own demo proved that is not
hypothetical (README §1).

**M4 is the hard one.** It is the bug persistence *causes*, and the check asserts the
**route** (`"month_total" in run.executed_names`) rather than only the destination. An
agent that guesses `12500` correctly and one that re-reads it look identical on one case
and diverge over a hundred.

---

## Acceptance checklist

- [ ] `uv run pytest 04_sessions_state -q` green, no API key needed
- [ ] `check_multiturn.py` — all five cases pass **in one run, on one model**
- [ ] `check_regression.py` — **Chapter 3's nine cases still pass against v4**
- [ ] `uv run ruff format . && uv run ruff check . && uv run pyright` all clean
- [ ] `solutions/RUNS.md` records the model name, the date, and real pasted output
- [ ] You can state which layer owns the stale-state fix, and why it is not a type

> **The regression rule is not a formality.** Chapter 3 broke Chapter 2's case 6 and only
> got caught because Chapter 2's cases were still in the dataset. `check_regression.py`
> exists so that catching it does not depend on anyone remembering to look.

---

## Challenges `[depth]` · 90 min

**1. Session expiry.** Conversations should not live forever. Add a rule — 24 hours of
silence starts a fresh conversation. Where does the timestamp live? (`SQLiteSession` does
not expose one. That is the exercise.)

**2. A per-user ledger.** Give `expense_store` a `user_id` and make every read filter by
it. Then answer honestly: how many of Chapters 1–3's cases did you have to touch, and what
does that tell you about where the seam should have been in Chapter 1?

**3. The two-tab problem.** Give one user two concurrent sessions that both log expenses.
Now have one ask for a total. Which of the two conversations is right? Neither — and
naming *why* is the answer.

---

# Track 3 — Your Own Agent `[core]` · 60 min

> **Same rubric, every chapter. Graded on evidence, never on features.**

```
Your Own Agent — Chapter 4 increment
  [ ] The chapter's capability is present and working in YOUR agent
  [ ] RUNS.md has 3 new runs, dated, with actual output pasted in
  [ ] One paragraph: what broke, and what you changed
  [ ] It is not an expense tracker
```

## What "the chapter's capability" means here

Both primitives, not one:

1. **A `SQLiteSession`**, file-backed, with a `session_id` you derived server-side from
   something the user cannot choose (README §4)
2. **A context object** carrying something *real* about the user — something that changes
   an answer. If your agent gives the same answer for two different contexts, the context
   is decorative and this box is not ticked
3. **At least one multi-turn run in `RUNS.md`** where turn 2 completes an action using a
   value supplied only in turn 1

## The paragraph

Answer these three, honestly:

- What did your agent do when you gave it memory that it did not do before?
- What did it start doing **wrong** that it did not do before? (If nothing: did you look?
  §8 exists because memory creates a new failure mode, not only a new capability.)
- Which piece of state did you initially put in the wrong one of session / context / store,
  and how did you find out?

> A student whose agent broke and who documented why has met the bar. A student with a
> working agent and no runs has not.

---

## 🔁 Spendly Transfer

In the real Spendly (`C:\Users\Faraz\Desktop\Spendly\`):

1. **A session keyed by phone number — hashed, not raw.** `session_id` is an authorisation
   decision wearing the costume of a cache key (README §4)
2. **A context object carrying the sender's timezone**, and one date-handling tool that
   reads it instead of trusting the server's clock. This is a real bug today: a user in
   Karachi logging an expense at 1am gets yesterday's date from a UTC server
3. **Measure before you optimise.** Log `len(await session.get_items())` per turn for a
   week and find your real p95. Chapter 5 will ask you for that number

**You're done when** a user can send `"500 at Metro"` and then `"groceries"` as two
separate WhatsApp messages and get one correctly logged expense.

---

## Session-by-session plan

| Session | Do | Ends when |
|---|---|---|
| 1 | README §1–§5, Exercises 1–2 | You can state the session/context difference without looking |
| 2 | README §6–§9, Exercise 4 | `check_multiturn.py` passes for you |
| 3 | README §10, Exercise 6, both tracks | `check_regression.py` green and `RUNS.md` written |
