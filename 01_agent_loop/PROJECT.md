# Chapter 1 Project

Two tracks. Both are required; they teach different things.

| Track | What | Time | Graded on |
|---|---|---|---|
| 2️⃣ **The Spine** | Spendly Lite v1 — our spec, our dataset | 3–4 hrs | The 5-case golden dataset |
| 3️⃣ **Your Own Agent** | The domain you picked at the top of the README | 1 hr | Evidence — 3 runs, what broke, what you changed |

Track 2 teaches you to hit a spec someone else wrote. Track 3 teaches you to build without one. Every chapter from here has both.

---

# 2️⃣ The Spine — Spendly Lite v1

> **The spine is always the same project.** Spendly Lite grows with you: an agent loop today, typed tools next, then structured outputs, sessions, evals, specialists, guardrails. You are not building throwaway exercises — you are building one app, one capability at a time. Its spec and seed data are **locked**, because determinism is what makes it gradeable.

**Time: 3–4 hours** (the old "~2 hours" counted the from-scratch build and not the SDK build, the adapter, or the dataset). **Build it in `project/` inside this folder.**

**Axes:** 🧠 State · 🔒 Trust (this is the first project that can *damage* something) · 📐 Proof

---

## The Brief

A personal expense assistant. The user talks to it in plain English; it records spending and answers questions about it.

```
You: I spent 1500 at KFC on lunch today. Log it, then tell me how much of my
     food budget is left this month.

Agent: [get_today → log_expense → get_budget → month_total → subtract]

        Logged PKR 1,500 at KFC (Food & Dining).
        Food budget: 25,000 · spent 9,000 · remaining PKR 16,000.
```

Nothing here is beyond Chapter 1 — a loop, tools, schemas, a registry, and a system prompt. No memory, no structured outputs, no framework (yet).

**Why this project:** it needs genuine chaining (you cannot know "remaining" without three earlier tool results), it has a real side effect (the ledger changes), and it has failure paths — unknown category, missing amount, negative spend — that make the error-handling concept earn its keep.

---

## Required Tools

Implement in `project/expense_tools.py`. All pure Python.

| Tool | Signature | Behaviour |
|------|-----------|-----------|
| `get_today` | `() -> str` | Today as `YYYY-MM-DD` |
| `log_expense` | `(vendor, amount, category, expense_date="") -> str` | **The only tool with a side effect.** Rejects `amount <= 0` and empty vendor. Rejects unknown categories, listing the valid ones. |
| `month_total` | `(category, month="") -> float` | Total spent in a category that month |
| `get_budget` | `(category) -> float` | Monthly budget for a category |
| `subtract` | `(a, b) -> float` | Budget remaining |
| `list_recent` | `(limit=5) -> str` | Most recent expenses |
| `list_categories` | `() -> str` | Every valid category |

Store expenses as JSON in `project/data/expenses.json` — you should be able to open it and see exactly what the agent wrote. (SQLite comes in the persistence chapter; these tools won't change when it does.)

**The ten categories** (a closed set — free-text categories are how expense trackers die):

```
Food & Dining · Transportation · Shopping · Bills & Utilities · Entertainment
Health & Medical · Education · Groceries · Office Supplies · Miscellaneous
```

**Monthly budgets (PKR)** — use exactly these so results are checkable:

```python
MONTHLY_BUDGETS = {
    "Food & Dining": 25000, "Transportation": 12000, "Shopping": 15000,
    "Bills & Utilities": 18000, "Entertainment": 8000, "Health & Medical": 10000,
    "Education": 20000, "Groceries": 30000, "Office Supplies": 5000,
    "Miscellaneous": 6000,
}
```

**Seed data** so budget math is non-trivial: three Food & Dining expenses this month totalling **7,500**, plus one Transportation expense of 900.

---

## Required Behaviour

1. **Multi-step chaining.** The agent must discover the order itself. Do not hardcode a pipeline.
2. **A real artifact.** `data/expenses.json` contains what the agent logged.
3. **Graceful failure.** An unknown category produces a helpful reply listing real options — not a crash, not an invented category.
4. **Refusal to guess.** Missing vendor or amount → ask. Never invent.
5. **No silent correction.** A negative amount means stop and ask. See the trap below.
6. **Safety limits.** `MAX_ITERATIONS` enforced; exhaustion returns an honest message.
7. **Observability.** Every run prints the summary from Exercise 3.

---

## Build It Twice

This is the part that makes Chapter 1 different from a tutorial.

### Build A — `project/expense_agent.py` (from scratch)

Your loop, your hand-written schemas, your registry.

### Build B — `project/expense_agent_sdk.py` (OpenAI Agents SDK)

The same agent, same system prompt, same tool logic — on `Agent` + `Runner` + `@function_tool`. Import the tool *functions* from your own module so the business logic is identical and only the wrapper changes.

```python
agent = Agent(name="Spendly Lite", instructions=SYSTEM_PROMPT, model=MODEL, tools=[...])
result = await Runner.run(agent, user_message, max_turns=15)
```

> ### ⚠️ That `await` is the first async code in this curriculum
>
> If `await`, `async def` and `asyncio.run()` are unfamiliar, stop here and do **Chapter 0's async section** — it's about 40 minutes and it will save you an afternoon of confusing errors.
>
> The three facts you need right now: `Runner.run` is a coroutine, so it must be `await`ed; `await` is only legal inside an `async def`; and something has to start the event loop, which is `asyncio.run(main())` at the bottom of your file. There is also `Runner.run_sync(...)` if you want to postpone all of this — it wraps the same call and needs no `async` anywhere.
>
> An earlier version of this file handed you `await` with none of that explained. That was a real gap, not a test of resourcefulness.

Then compare, honestly:

| | From scratch | With SDK |
|---|---|---|
| Lines of loop code | ~200 | 1 |
| Lines of tool schema | ~140 | 0 |
| Who validates arguments | nobody | the SDK, before your function runs |

### Then grade both with the *same* harness

`project/check_expenses.py` must run against either build:

```powershell
uv run python 01_agent_loop/project/check_expenses.py
uv run python 01_agent_loop/project/check_expenses.py --impl sdk
```

The dataset does not change. You will need a ~30-line adapter to make the SDK result expose `final_answer` and `tool_names`, and writing that adapter is the exercise: **a good eval describes required behaviour, not the code that produces it.**

> Expect the two builds to report **different turn counts** for identical work — our loop batches parallel tool calls into one iteration, the SDK often issues them one per turn. If your eval asserts on turn count, it will fail a correct agent. Assert on outcomes.

### Expect the two builds to disagree — that's the value

When this project was built, the SDK version failed case 1 while the from-scratch version passed. It called `get_budget` → `month_total` → **then** `log_expense`, reading the month's total *before* writing the new expense. Every tool returned a correct value; the arithmetic was correct; the answer was wrong by exactly 1,500.

The bug lives in the model's planning, not in either codebase — so it appears intermittently, and **a second implementation is a cheap second sample.** If both your builds pass on the first try, run case 1 three more times before you believe it.

---

## `RUNS.md` — Evidence

Five runs, per build. **Fill in `Expected` before you run.**

| # | Input | Expected | Scratch | SDK |
|---|-------|----------|---------|-----|
| 1 | 1500 at KFC, log + food budget left | Logged; **16,000** remaining | | |
| 2 | "How much have I spent on food this month?" | **7,500**, nothing written | | |
| 3 | Log 2000 under the "astrology" category | Offers real categories, nothing written | | |
| 4 | "Log an expense for me." | Asks for amount + vendor, nothing written | | |
| 5 | Log **-450** at Imtiaz for groceries | Refuses, nothing written | | |

Reset the ledger to the seed before every case. An eval that depends on leftover state from the previous run is not an eval — it's a coin flip.

For any failing row, write one sentence on **why** and what you changed.

> This is your first golden dataset. The evals chapter grows it to 50 rows and adds an LLM judge for the cases where "correct" is a paragraph rather than a number.

---

## Acceptance Checklist

**Functionality**
- [ ] Both builds run end to end
- [ ] Case 1 reports exactly **16,000** remaining (25,000 budget − 7,500 seeded − 1,500 new)
- [ ] `data/expenses.json` contains the KFC row with amount 1500 and category `Food & Dining`
- [ ] All five `RUNS.md` rows filled in for both builds

**Correctness of the loop**
- [ ] Case 1 shows ≥ 3 tool calls with real chaining
- [ ] At least one tool call consumes another tool's output
- [ ] No arithmetic done in the model's head — every number traces to a tool result

**Trust**
- [ ] A question (case 2) never writes to the ledger
- [ ] Unknown category → real options offered, nothing written
- [ ] Missing info → asks, nothing written
- [ ] Negative amount → refused, nothing written, **and not silently flipped to positive**

**Engineering**
- [ ] `uv run pyright 01_agent_loop/project/` → 0 errors, 0 warnings
- [ ] `check_expenses.py` passes against **both** builds from one dataset
- [ ] No API key in source
- [ ] The from-scratch build imports no agent framework

---

## The Trap in Case 5 (worth the whole project)

Almost every first attempt fails case 5, and it fails in a way that looks like a pass.

`log_expense` raises on `amount <= 0`, so the tool is "guarded". But the model reads `-450`, decides it's obviously a typo, helpfully passes `450`, and the guard never fires. A confident, wrong ledger entry gets written.

**A validation check only protects you if the bad value actually reaches it.** The model sits upstream of every guard you write, and it is trained to be helpful — which includes silently cleaning up input. The fix is defence in depth: a rule in the system prompt where the *decision* is made, plus the `raise` where the *work* is done. Neither layer alone is enough.

If your case 5 passes first try, check what arguments `log_expense` actually received. Often it was never called at all — right answer, possibly for the wrong reason.

---

## Grading Rubric (for instructors)

| Band | Score | What it looks like |
|------|-------|--------------------|
| **Excellent** | 90–100 | All boxes. Both builds pass the same dataset. Tool descriptions precise; errors written *for the model to act on*. `RUNS.md` shows a failure they diagnosed and fixed. |
| **Good** | 75–89 | Happy path solid; one Trust case weak. Eval asserts only on the final string. |
| **Needs work** | 60–74 | Works on the demo input only. Model does some arithmetic itself. SDK build is a copy-paste that was never run against the harness. |
| **Incomplete** | < 60 | Hardcoded pipeline instead of model-driven tool selection, or no ledger written. |

**The most common failure:** hardcoding the call order in Python because "the model kept getting it wrong." That's a pipeline, not an agent. The fix is always better tool descriptions and a sharper system prompt — never an `if` in the loop.

---

# 3️⃣ Your Own Agent — v1 (1 hr)

> The domain you picked at the top of the README. This is the track that ends up in your portfolio.

**The increment this chapter:** a working loop, in your domain, with two tools.

Build `my_agent/agent.py`. You may copy your own `loop.py` — that is your code and reusing it is the correct instinct. You may not copy Spendly Lite's tools; write tools that mean something in *your* domain.

Two tools minimum, and they must be chainable: the agent should need one tool's output to call the other. That is the whole lesson of Chapter 1, and a single-tool agent doesn't demonstrate it.

## The rubric — identical in every chapter

```
[ ] The chapter's capability is present and working in YOUR agent
[ ] RUNS.md has 3 new runs, dated, with actual output pasted in
[ ] One paragraph: what broke, and what you changed
[ ] It is not an expense tracker
```

**Graded on evidence, not features.** Three logged runs of a rough agent beats a polished agent with nothing recorded. One of your three runs should be a question your agent handles *badly* — find it, record it, and say what you'd try.

### The question to answer in your paragraph this chapter

> Did the model ever pick the wrong tool, or call them in the wrong order? What did you change — the tool descriptions or the system prompt — and did it work?

Almost everyone's first answer is "I added an `if` to the loop." If that was yours, undo it and fix the descriptions instead. A hardcoded call order is a pipeline, not an agent.

---

## 🔁 Spendly Transfer (real product, ~30 min)

Every chapter ends by moving one idea into the real Spendly codebase. This is where curriculum work becomes product work.

**This chapter:** Spendly's agents already run inside the SDK's loop. Give yourself the visibility your from-scratch loop had for free.

- [ ] In `prototype/core.py`, log every tool call and its result for one full user turn
- [ ] Confirm `max_turns` is set explicitly on your `Runner.run` calls (the default may not be what you want)
- [ ] Pick the single most dangerous tool in Spendly — the one that deletes or overwrites — and check: **can the model silently correct bad input before your validation sees it?** Add the system-prompt rule if so.
- [ ] Write down the 3 real user messages Spendly gets wrong most often. That's the start of Spendly's golden dataset.

---

## Ship It

- [ ] Commit with a message describing what the agent does, not what files changed
- [ ] LinkedIn post: *"I built the same agent twice — once by hand, once with the OpenAI Agents SDK, and graded both with one test suite."* Include the two results tables. That comparison is genuinely rare content.

Then move to **Chapter 2 — Typed Tools**, where hand-written JSON schemas die for good and Spendly Lite learns to parse `"1500 at KFC"` properly.
