# Chapter 2 Project

Two tracks. Both are required; they teach different things.

| Track | What | Time | Graded on |
|---|---|---|---|
| 2️⃣ **The Spine** | Spendly Lite v2 — locked spec, locked dataset | 2.5 hrs | The 7-case golden dataset, **plus Chapter 1's 5 cases still passing** |
| 3️⃣ **Your Own Agent** | The domain *you* picked in Chapter 1, v2 | 1 hr | Evidence — 3 runs, what broke, what you changed |

Track 2 teaches you to work inside a spec someone else wrote and not break what already worked. Track 3 teaches you to build without one. Doing only one of them leaves a real gap.

---

# 2️⃣ The Spine — Spendly Lite v2

> **The increment:** Spendly Lite's tools stop trusting the model.
>
> You do not start a new project. You take v1 from Chapter 1 and give it a boundary.

---

## The brief

Rebuild Spendly Lite's seven tools so that **no invalid call can reach a function body**, and so that a rejected call teaches the model enough to fix itself.

Build it **twice** — once from scratch, once on the SDK — and grade both with **one** dataset.

| | v1 (Chapter 1) | v2 (this chapter) |
|---|---|---|
| Tool schemas | ~110 lines, hand-written | generated from signatures |
| Category enforcement | a sentence in a `description` | `Literal` — in the schema, checked at the door |
| Negative amounts | an `if` inside the function | `Field(gt=0)` |
| Bad arguments | `TypeError` → the model sees a Python internal | `ToolError` → the model sees an instruction |
| A rejected call | may have half-executed | provably no side effects |
| Unit tests | none possible | ~45, no API key, under 3 seconds |
| Evals | 5 cases | 7 cases, asserting on *executed* vs *attempted* |

---

## What you must build

### 1. `expense_store.py` — carry it forward, one change

The store does not change. Add exactly one thing:

```python
Category = Literal["Food & Dining", ...]
CATEGORIES: tuple[str, ...] = get_args(Category)
```

The runtime tuple must be **derived** from the type, not typed out again.

> If the validation layer forces you to rewrite your storage, the validation layer is wrong. A tool should stay a thin wrapper over business logic you could equally call from a web app or a cron job.

### 2. `expense_tools.py` — the seven tools, under contract

All seven from v1: `get_today`, `log_expense`, `month_total`, `get_budget`, `subtract`, `list_recent`, `list_categories`.

Requirements:

- **Zero** hand-written JSON Schema.
- Named `Annotated` aliases for the recurring constraints — `Vendor`, `Amount`, `IsoDate`, `Month`, `Limit`. A signature made of raw `Annotated[...]` is unreadable at seven arguments.
- `Amount` must reject `true`. Find out why before you write the fix.
- Exactly **one** hand-written guard should survive in the whole file. Know which one, and be able to say why it could not move into a type.

### 3. `loop.py` — the loop, with a boundary

Take Chapter 1's `loop.py` and change four things:

- `tools: list[Tool]` replaces `tool_registry` + `tool_schemas`
- dispatch through `tool.call(raw)`
- `ToolCallRecord.rejected` — did this call reach a function body?
- `MAX_INVALID_CALLS` — a budget on wrongness, separate from the budget on length

Keep the 429 backoff and the wall-clock ceiling. New capability should cost new code, not a rewrite.

`AgentRun` must expose **`executed_names`** as well as `tool_names`. Chapter 1 could not tell those apart; your evals now depend on the difference.

### 4. `test_expense_tools.py` — the proof, and the cheap kind

At least **20 attack payloads** and **6 happy paths**, running with no API key in under 3 seconds.

Plus at least **four** assertions on the **schema** rather than the behaviour:

```python
def test_category_enum_reaches_the_schema() -> None:
    enum = log_expense.parameters["properties"]["category"]["enum"]
    assert set(enum) == set(CATEGORIES)
```

> A tool can behave perfectly and still be broken, if the contract it published to the model was wrong. Behaviour tests will never catch that.

### 5. `expense_agent_sdk.py` — the same agent on the SDK

Same seven tools with `@function_tool`, reusing the **same** `Annotated` aliases, calling the **same** business logic. Hold the logic constant or the comparison is dishonest.

Must include a `failure_error_function`. Using the SDK default is a fail — the point of the layer is that you saw the default and made a decision about it.

### 6. `check_expenses.py` — 7 cases, one dataset, two builds

Chapter 1's five, plus:

- **a recovery case** — the model sends something the schema forbids, reads the rejection, and fixes it
- **a "types cannot hold this" case** — the future date

Every check on "did it happen" must use `executed_names`, not `tool_names`.

### 7. `RUNS.md` — the evidence

Paste the real result tables from both builds. Not a summary — the actual output, with the date and the model name.

---

## Acceptance checklist

Tick every box. Each is checkable by someone else.

### The boundary

- [ ] `uv run pytest 02_typed_tools/` passes with ≥26 tests in under 3 seconds
- [ ] no test in that file requires an API key
- [ ] every attack payload asserts **both** that it raised **and** that the ledger is unchanged
- [ ] `log_expense.call('{"vendor": "KFC", "amount": true, "category": "Food & Dining"}')` is rejected
- [ ] `log_expense.call('{"vendor": "KFC", "amount": "1500", "category": "Food & Dining"}')` **succeeds**, and you can say why the two lines above are not inconsistent

### The contract

- [ ] `grep -c '"type": "object"' expense_tools.py` returns `0` — no hand-written schema survives
- [ ] every tool's schema has `additionalProperties: false`
- [ ] the category `enum` in the schema has exactly 10 values and matches `CATEGORIES`
- [ ] no Pydantic constraint names (`gt`, `ge`, `min_length`, …) leak into any schema
- [ ] every tool has a non-empty description

### The agent

- [ ] `uv run python 02_typed_tools/solutions/check_expenses.py` → **all checks pass**
- [ ] `uv run python 02_typed_tools/solutions/check_expenses.py --impl sdk` → **all checks pass**
- [ ] one dataset graded both; you did not weaken a check to make a build pass
- [ ] at least one recorded run shows a rejection **followed by a successful retry**
- [ ] **the regression rule:** Chapter 1's five cases still pass. A chapter that breaks the previous chapter's dataset is not done, however good its new features are

### The gate

- [ ] `uv run ruff format .` — clean
- [ ] `uv run ruff check .` — clean
- [ ] `uv run pyright` — 0 errors, 0 warnings
- [ ] `uv run pytest` — green

### The understanding

- [ ] you can name the one guard that could not move into a type, and the general rule behind it
- [ ] you can state what `strict_json_schema=True` does and why it does not make your validation redundant
- [ ] you can explain why an eval asserting `"log_expense" in run.tool_names` is now wrong

---

## Rubric

| Grade | What it looks like |
|---|---|
| **Not yet** | Tools are typed, but validation still happens inside function bodies. Tests need an API key. `tool_names` used where `executed_names` was needed. |
| **Pass** | Both builds pass the 7 cases. Schema is generated. Tests run offline. The gate is green. |
| **Strong** | The error messages are written for a model and it visibly recovers from them in a recorded run. Schema-level tests exist. The one surviving hand-guard is deliberate and documented. |
| **Distinction** | An attack in your own test file found a real gap in your tools before any agent did — and `RUNS.md` shows the before and after. You can argue where validation *should* stop, not just where you put it. |

---

## 📐 RUNS.md — what to record

```markdown
# Spendly Lite v2 — run evidence

Model: gemini-2.5-flash   Date: 2026-08-13

## Unit tests (no API)
46 passed in 1.90s

## Golden dataset — from scratch
| # | Checks | Tools executed | Rejected | Turns | Pass? |
...

## Golden dataset — Agents SDK
| # | Checks | Tools executed | Rejected | Turns | Pass? |
...

## One rejection, in full
(paste the tool call, the rejection message, and the model's next call)

## What differed between the two builds
...
```

That last section is the one worth writing carefully. The two builds will not behave identically — different turn counts, different tool ordering, sometimes different rejection counts. **Every difference you can explain is a thing you understand about the SDK.**

---

# 3️⃣ Your Own Agent — v2

> The agent you started in Chapter 1, in **your** domain. SDK-only, blank file, no scaffolding from us.

**The increment this chapter:** your tools stop trusting the model.

Whatever your agent does — a recipe planner, a workout logger, a D&D companion, a study-schedule builder — it has at least one tool where a wrong argument matters. Give that tool a real contract:

- every closed set is a `Literal`
- every range or format is `Annotated[..., Field(...)]`
- **zero `if` statements** doing work a type could do
- one `failure_error_function`, on the tool where you decided the model needs the detail

Then break it on purpose and write down what happened.

## The rubric — identical in every chapter

```
[ ] The chapter's capability is present and working in YOUR agent
[ ] RUNS.md has 3 new runs, dated, with actual output pasted in
[ ] One paragraph: what broke, and what you changed
[ ] It is not an expense tracker
```

**You are graded on evidence, not features.** An agent that broke in an interesting way, with the breakage documented and understood, passes this. A polished agent with no `RUNS.md` does not.

At least one of your three runs must be a **deliberate attack** on your own tool — send it something a confused model would plausibly send, and record what came back.

### The question to answer in your paragraph this chapter

> Which of your tool's rules could **not** move into a type, and where did you have to put it instead?

Every real agent has at least one. Finding yours is the point.

---

## 🔁 Spendly Transfer

Into the real Spendly codebase (`C:\Users\Faraz\Desktop\Spendly\`):

1. Pick the **one** tool that writes to the database — the one where a bad argument is permanent.
2. Give it a Pydantic args model: closed sets as `Literal`, ranges as `Field`, no `if` statements for anything a type can hold.
3. Write **10 attack payloads** against it as a pytest file. No API key, under a second.
4. Run them. Fix whatever they find.
5. Record in one line: how many of the 10 found something.

> This is a ~90 minute task and it is the highest-value hour in the chapter. Spendly writes real expenses for a real user. Every attack that fails today is one that does not become a support message later.

---

## Where next

Chapter 3. Your tools now reject bad **input**. Nothing yet checks the agent's **output** — the final message to the user is still free-form prose that no schema has ever seen.
