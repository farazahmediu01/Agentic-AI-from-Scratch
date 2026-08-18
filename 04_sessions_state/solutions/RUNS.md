# Spendly Lite v4 — run evidence

**Model:** `gemini-3.5-flash-lite` (Gemini free tier, Chat Completions)
**Date:** 2026-08-18
**Commands:**

```powershell
uv run pytest 04_sessions_state -q
uv run python 04_sessions_state/solutions/check_multiturn.py
uv run python 04_sessions_state/solutions/check_regression.py
```

## Unit tests (no API key, ~1s)

```
13 passed          # 04_sessions_state only
86 passed          # whole repo
```

## Multi-turn dataset — 5 cases, one run

```
CASE M1: the answer to Chapter 3's question
  TURN 1  branch=need_more_info  turns=1  items=2   in_tok=1,942
  TURN 2  branch=logged          turns=6  items=14  in_tok=12,924

CASE M2: the control - no session
  TURN 1  branch=need_more_info  turns=1  items=0   in_tok=1,942
  TURN 2  branch=need_more_info  turns=1  items=0   in_tok=1,937

CASE M3: session isolation
  TURN 1  branch=need_more_info  turns=1  items=2   in_tok=1,942
  TURN 2  branch=need_more_info  turns=1  items=2   in_tok=1,937

CASE M4: stale state
  TURN 1  branch=reported        turns=2  items=8   in_tok=4,005
          [the world changed between turns]
  TURN 2  branch=reported        turns=4  items=24  in_tok=9,407

CASE M5: the context decides the answer
  TURN 1  [Faraz]   branch=reported  turns=3  items=0  in_tok=6,034
  TURN 2  [Ayesha]  branch=reported  turns=3  items=0  in_tok=6,108

36/36 checks passed
All cases passed.
```

Read M1 and M2 side by side. Same two prompts, same agent, same model. The only
difference is `session=`, and it is the difference between a logged expense and a
second question.

M5's two turns are the same sentence sent to the same agent object, and the
assertions that passed were `Faraz: remaining == 17500` and
`Ayesha: remaining == 1500`.

## Regression — Chapter 3's 9 cases, against Chapter 4's agent

```
CASE 1  branch=logged           turns=6   rejected=0
CASE 2  branch=reported         turns=6   rejected=0
CASE 3  branch=refused          turns=2   rejected=0
CASE 4  branch=need_more_info   turns=1   rejected=0
CASE 5  branch=refused          turns=2   rejected=0
CASE 6  branch=logged           turns=2   rejected=0
CASE 7  branch=refused          turns=1   rejected=0
CASE 8  branch=need_more_info   turns=1   rejected=0
CASE 9  branch=refused          turns=2   rejected=0

58/58 checks passed
All cases passed. Chapter 3's behaviour survived Chapter 4.
```

Not one of those cases was copied or edited. `check_regression.py` imports `CASES`
from Chapter 3 and pushes them through v4's `run_expense_agent`. It is forty lines
because Chapter 3's harness declared a `Protocol` instead of importing its concrete
`SdkRun` — a decision that looked like ceremony at the time and paid for itself one
chapter later.

## What the verification run found

Getting to 36/36 took three attempts. **None of the three failures was in the
mechanism the chapter teaches**, and two of them were in this file's own harness.

### Attempt 1 — 2/9 on M1, and it looked exactly like a broken agent

The harness built and **cleared** its session inside the turn loop, so turn 1 was
wiped before turn 2 ran. M1 came back `branch=need_more_info`, which is
indistinguishable from an agent that cannot use its memory.

The only reason the harness got suspected before the prompt is that the same two
turns had passed by hand in `expense_agent_v4.main()` minutes earlier.

> **Reset per CASE, never per TURN.** A multi-turn harness has two clocks, and
> mixing them up produces a failure that reads as a model problem.

### Attempt 2 — a check that was wrong about its subject, not its threshold

M3 asserted `session_items <= 2` as a proxy for *"the other conversation did not
leak in"*, and failed at 6 — because a run appends its own items to the session it
runs in. The count was measuring the wrong conversation.

Raising the number would have produced a green check that no longer tested
isolation at all: `session_items <= 8` passes just as happily when the other
conversation **has** leaked in. Fixed by adding `session_text` to `SdkRun` and
asserting the actual claim, `"Metro" not in run.session_text`.

> **Never weaken a check to make a run pass.** If a check is wrong, it is usually
> wrong about *what* it asserts.

### Attempt 3 — the control caught the fix that made the main case pass

M2 failed with `branch=logged  turns=8`. With **no session**, given only
`"Groceries."`, the agent called `log_expense` with a vendor and an amount nobody
had ever supplied.

The cause was a prompt rule added *for M1*:

```
If you asked which category an expense belongs to and the user answers with a
category name, that answer belongs to the expense you were asking about --
complete it and log it.
```

With an empty transcript the model reasons: the user said "Groceries.", so I must
have asked, so I complete it — and backfills the rest.

> **A rule written to exploit memory becomes an instruction to invent when the
> memory is absent.** The rule never said *"check that you can actually see it"*.
> It did not need to while every test had a session attached.

This is the fourth member of a family that now spans three chapters:

| Where | The model… |
|---|---|
| Ch2 §7b | **fabricated** a value from nothing |
| Ch3 §1 | **miscomputed** one from real tool output |
| Ch3 case 8 | **inferred** a plausible one from context |
| **Ch4 M2** | **backfilled** one from a conversation that never happened |

Fixed in the prompt — correctly, because the reply was a flawless `Logged` and no
schema could have objected. Only the world it described was imaginary.

**M1 was re-run immediately after the fix and still scored 10/10.** Narrowing a
rule is exactly the change that over-corrects; Chapter 3 learned that when the
case-6 fix threatened case 7, and checking is the point.

## Two environment findings, both measured

**Not every model can run this spine.** From Chapter 3 on it needs `output_type=`
**and** tools *together*. `gemini-2.5-flash` refuses the combination:

```
400 INVALID_ARGUMENT
"Function calling with a response mime type: 'application/json' is unsupported"
```

That is a 400, not a 429 — it has nothing to do with quota, and it cost a full run
after being chosen as a "fresh bucket".

**The daily free-tier cap is per model and differs enormously.** Read `quotaValue`
in the 429 body:

| Model | Daily cap | Fits a dataset run (60–90 requests)? |
|---|---|---|
| `gemini-3.5-flash-lite` | **500** | yes — the curriculum default, for this reason |
| `gemini-3.5-flash` | **20** | no |

So *"switch to any other model for a fresh bucket"* was wrong on its own. Switch to
a model you have checked, and probe an untested one with a single request before
betting fifteen minutes on it.

Both limits appeared in this session and they need different fixes:

| quotaId | Limit | Fix |
|---|---|---|
| `...PerMinutePerProjectPerModel-FreeTier` | 15/min | pacing — killed `session_demo.py` |
| `...PerDayPerProjectPerModel-FreeTier` | model-specific | a different, verified model |

Same status code, same exception class.
