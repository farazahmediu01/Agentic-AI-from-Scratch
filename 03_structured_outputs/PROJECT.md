# Chapter 3 Project

Two tracks. Both required; they teach different things.

| Track | What | Time | Graded on |
|---|---|---|---|
| 2️⃣ **The Spine** | Spendly Lite v3 — **SDK-only from this chapter on** | 2 hrs | The 9-case dataset, **plus Chapters 1–2's cases still passing** |
| 3️⃣ **Your Own Agent** | Your domain, v3 | 1 hr | Evidence — 3 runs, what broke, what you changed |

---

# 2️⃣ The Spine — Spendly Lite v3

> **The increment:** Spendly's answers stop being prose.

## ⚠️ Read this first — the spine stops being built twice

Chapters 1 and 2 built Spendly Lite **twice**, by hand and on the SDK, graded by one dataset. That earned its keep: a second implementation of a non-deterministic system is a second behavioural sample, for free.

**This chapter is where it stops.** The reason is specific, not fatigue:

The hand-rolled version of *this* mechanism is `from_scratch/prompt_and_parse.py`, and §3 spends twenty-five minutes proving it cannot be made correct. Building the spine on top of it — to preserve a symmetry — would mean shipping a practice the chapter had just finished disproving.

So from here:

| | Before | From Chapter 3 |
|---|---|---|
| The spine | two implementations | **one, on the SDK** |
| The hand-rolled layer | a real, maintained build | a disposable spike, deleted after the chapter |

`from_scratch/prompt_and_parse.py` may be deleted the moment §4 makes sense. It is not imported by anything. This is written into `CLAUDE.md` as **The Taper Rule**, and it was decided as design rather than discovered as exhaustion.

## The brief

Give every Spendly reply a shape, and convert the golden dataset from substring matching to field assertions.

| | v2 (Chapter 2) | v3 (this chapter) |
|---|---|---|
| The final answer | free-form prose | a `SpendlyReply` object |
| "Did it log or report?" | grep the sentence | `reply.branch` |
| "Did it ask for the right thing?" | unanswerable | `reply.need_more_info.missing` |
| "Why did it refuse?" | search 8 synonyms | `reply.refused.reason` |
| Eval assertions | substrings | fields |
| Dataset | 7 cases | 9 |
| Builds | two | one |

## What you must build

### 1. `replies.py` — the output contract

Four branches: `Logged`, `Reported`, `NeedMoreInfo`, `Refused`.

Requirements:

- Every value the agent might legitimately not have is `| None` or lives in its own branch. **A required field is an instruction to always have an answer.**
- Every closed set is a `Literal` — the refusal reason, the missing-field names, the category.
- `Category` is imported from Chapter 2's `expense_store`, not retyped. Same closed set, now constraining an output.
- A `model_validator` enforcing **exactly one branch**. Know why this cannot live in the schema.

### 2. `expense_agent_v3.py` — the agent

Chapter 2's seven tools, unchanged, plus `output_type=SpendlyReply`.

The prompt gains exactly one section: **which branch means what.** It must not describe the JSON format, list the keys, or ask for valid syntax — the schema owns all of that.

> That division is the chapter in one line: **shape moved into the type; judgement stayed in the prompt, because it was always judgement.**

### 3. `check_expenses.py` — 9 cases, all asserting on fields

Chapter 2's seven, converted, plus:

- **a precision-of-the-ask case** — vendor and amount given, category missing, asserting `missing == ["category"]` exactly
- **a refusal-classification case** — asserting on the reason enum, not on prose

**No check may use `in answer`.** If you cannot express an assertion as a field comparison, that is a signal your output model is missing a field.

### 4. `test_replies.py` — the free layer

Offline tests, no API key, under 2 seconds:

- zero branches rejected, two branches rejected, one accepted
- every `Literal` rejects a near-miss value
- at least one assertion on the **schema** rather than behaviour
- **one test that passes while being a lie** — the §8 lesson, in executable form

### 5. `RUNS.md` — the evidence

The real 9-case table with the date and model name. Plus one run pasted in full showing the typed reply object, and one paragraph on any case that behaved differently from v2.

---

## Acceptance checklist

### The contract

- [ ] `result.final_output` is a `SpendlyReply`, never a string
- [ ] no field forces the model to invent a value it cannot have
- [ ] `exactly_one_branch` rejects `{}` and rejects two branches, with tests for both
- [ ] the category enum in the **output** schema matches `CATEGORIES`
- [ ] the prompt contains no description of JSON syntax

### The dataset

- [ ] `uv run python 03_structured_outputs/solutions/check_expenses.py` → all 9 pass
- [ ] **the regression rule:** Chapters 1 and 2's cases still pass, converted but not weakened
- [ ] zero assertions use substring matching
- [ ] you did not relax a check to make a run pass

### The honest limit

- [ ] you have a test that **passes on fabricated data**, and you can explain why it is there
- [ ] you built Practice 8's `verify_reply` cross-check and have one run where it found a real discrepancy

### The gate

- [ ] `ruff format` · `ruff check` · `pyright` (0/0) · `pytest` — all clean

---

## Rubric

| Grade | What it looks like |
|---|---|
| **Not yet** | `output_type` is set but the model has required fields the agent cannot always fill. Evals still grep. One rigid shape with no refusal branch. |
| **Pass** | Four branches, exactly-one enforced, 9 cases green on field assertions, earlier chapters still passing. |
| **Strong** | Optionality is deliberate and defensible field by field. The cross-check from Practice 8 exists and has caught something. Schema-level tests. |
| **Distinction** | You found a case where the agent produced a valid, well-typed, **false** reply, recorded it in `RUNS.md`, and can say precisely which layer would have to catch it — and why it is not this one. |

---

# 3️⃣ Your Own Agent — v3

> Your domain. SDK-only, blank file.

**The increment:** your agent's replies get a shape, including a shape for *"I can't."*

- an output model with **at least three branches**, one of which is a refusal or an ask
- every optional value actually optional — audit each field with *"what does it put here when it doesn't know?"*
- every closed set a `Literal`
- a `model_validator` enforcing exactly one branch

## The rubric — identical in every chapter

```
[ ] The chapter's capability is present and working in YOUR agent
[ ] RUNS.md has 3 new runs, dated, with actual output pasted in
[ ] One paragraph: what broke, and what you changed
[ ] It is not an expense tracker
```

One of your three runs must be a prompt where the honest answer is **"I don't have enough to answer that."** Record which branch the agent chose.

### The question to answer in your paragraph this chapter

> Which field in your output model did the agent fabricate first, and what made it fabricate — a required field, a missing branch, or a prompt that asked instead of a type that constrained?

---

## 🔁 Spendly Transfer (real product, ~60 min)

Into the real Spendly codebase (`C:\Users\Faraz\Desktop\Spendly\`):

1. Find the agent whose reply gets parsed, string-matched, or regexed by downstream code. There is always one.
2. Give it an `output_type` with a union that includes the honest failure branch — whatever "I couldn't do that" means in Spendly.
3. Delete the parsing code it replaces. Count the lines.
4. Find one WhatsApp reply Spendly has sent that was well-formed and wrong. Write the cross-check that would have caught it.
5. Record in one line: lines of parsing deleted, and whether the cross-check found anything on real traffic.

> Step 4 is the valuable one. Spendly talks to a real user, and a confidently wrong number in a WhatsApp message is exactly the failure §8 describes.

---

## Where next

Chapter 4. Your agent's input has a contract and its output has a contract — and it still forgets everything the moment a run ends. A reply that says `missing: ["category"]` is only useful if something remembers what it was asking about.
