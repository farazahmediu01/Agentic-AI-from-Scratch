# Spendly Lite v3 — run evidence

**Model:** `gemini-3.5-flash-lite` (Gemini free tier, Chat Completions)
**Date:** 2026-08-17
**Command:** `uv run python 03_structured_outputs/solutions/check_expenses.py`

## Unit tests (no API key)

```
73 passed in ~2s
```

## Golden dataset — 9 cases, one run

```
CASE 1  branch=logged           turns=6   rejected=0
CASE 2  branch=reported         turns=4   rejected=0
CASE 3  branch=refused          turns=2   rejected=0
CASE 4  branch=need_more_info   turns=2   rejected=0
CASE 5  branch=refused          turns=1   rejected=0
CASE 6  branch=logged           turns=3   rejected=0
CASE 7  branch=refused          turns=1   rejected=0
CASE 8  branch=need_more_info   turns=2   rejected=0
CASE 9  branch=refused          turns=2   rejected=0

58/58 checks passed
All cases passed.
```

Cases 1–7 are Chapter 2's, converted from substring assertions to field
assertions. Cases 8–9 could not have been written before this chapter.

## What the verification run found

Getting to 58/58 took three attempts, and the first two failed for reasons
worth recording — none of which was the mechanism the chapter teaches.

### Attempt 1 — 25/58, and the agent was fine

Seven cases failed with `branch=none turns=0`. Under sustained rate limiting
the SDK absorbs the 429, hands the run loop an unusable response, and burns
`max_turns` in seconds — so what escapes is `MaxTurnsExceeded`, not
`RateLimitError`. A quota problem arrives wearing the costume of a runaway
agent, and the retry wrapper was catching the wrong exception.

**The tell is the clock.** Real max-turns exhaustion takes a while. Quota
exhaustion is instant.

### Attempt 2 — two real defects, found by the new assertions

**Case 8 — the agent inferred a category nobody gave it.** `"Log 500 at
Metro."` supplies vendor and amount and no category; the agent inferred one
from the vendor name and wrote it. The prompt covered *"names a category that
does not exist"* and said nothing about *"names none"*. This is the first case
in the curriculum that ever probed that gap.

**Case 6 — Chapter 3 regressed Chapter 2.** A date written
`05/08/2026 (the 5th of August)` is unambiguous but in a forbidden format.
Chapter 2 recovered from it. Chapter 3 refused it on turn one without
attempting the call — because `refused` had become a well-typed, blameless,
obviously-correct-looking option.

> A rigid single output shape creates **fabrication pressure**. A refusal
> branch creates **refusal pressure**. Every branch you add is a road you have
> paved, and traffic will use it.

Both fixes were **prompt changes, not type changes**, because both failures
were judgement rather than shape. Case 7 was re-run after the case 6 fix to
confirm the legitimate refusal still fires — narrowing a refusal rule is
exactly the change that over-corrects.

### The free-tier limit that actually blocks this

Not the famous one. `GenerateRequestsPerDayPerProjectPerModel-FreeTier`,
**500 requests per day**. One full dataset run is 60–90 requests.

The bucket is per **project** and per **model**, so switching `MODEL_NAME` to
a different Gemini model gives a fresh 500 immediately. A second API key from
the same project does not.

Two runs were lost to backoff tuned against the per-minute limit while the
per-day limit was the actual wall. **Read the `quotaId` in a 429 before you
tune a retry.**

## Why this run matters beyond Chapter 3

Case 6 was caught **only because Chapter 2's cases are still in Chapter 3's
dataset.** A curriculum that started a fresh dataset per chapter would have
shipped a chapter that silently broke the previous one's behaviour.

That is the regression rule earning its keep on its first real opportunity,
on this repository's own code.
