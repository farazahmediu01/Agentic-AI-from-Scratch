# Step 1 — Reference Solutions & Answer Key

> **Students: attempt first.** Reading a solution feels like learning and isn't. If you're stuck, re-read the concept the task sits under, then try again for 10 more minutes before opening anything here.
>
> **Instructors:** this is your grading reference and your debrief script.

## Files

All paths below are relative to the repo root; run them with `uv run python <path>`.

| File | Solves | Run it |
|------|--------|--------|
| `loop.py` | The shared reference loop — returns `AgentRun`, takes tools as parameters, retries 429s | (imported) |
| `unit_tools.py` / `unit_agent.py` | Exercise 4 — Unit Converter Agent | `01_agent_loop/solutions/unit_agent.py` |
| `check_agent.py` | Exercise 5 — structured trace + assertions | `01_agent_loop/solutions/check_agent.py` |
| `expense_store.py` | Spendly Lite storage + seed data + `reset()` | (imported) |
| `expense_tools.py` | Spendly Lite tools, hand-rolled schemas | (imported) |
| `expense_agent.py` | **Project, from-scratch build** | `01_agent_loop/solutions/expense_agent.py` |
| `expense_agent_sdk.py` | **Project, Agents SDK build** | `01_agent_loop/solutions/expense_agent_sdk.py` |
| `check_expenses.py` | The 5-case golden dataset — grades **either** build | `01_agent_loop/solutions/check_expenses.py [--impl sdk]` |
| `invoice_*.py`, `check_invoice.py` | Superseded first draft of the project (kept for reference) | |

Exercises 1–3, 6 and 7 are intentionally **not** solved in code — they're small edits or open designs, and the answer key below covers what matters.

### Verified state (last run 2026-08-12)

| Build | Result |
|---|---|
| from scratch | **24/24 checks, 5/5 cases** |
| OpenAI Agents SDK | **24/24 checks, 5/5 cases** |

One dataset, two implementations, same verdict. That equivalence is the chapter's closing argument.

### The one thing to notice in `loop.py`

The tool registry and schemas are **parameters**, not imports:

```python
def run_agent(user_message, tool_registry, tool_schemas, system_prompt=None): ...
```

That single change is why one loop drives both the unit agent and the invoice agent. It is also, almost exactly, what a framework's `Agent(tools=[...])` constructor buys you. Worth saying out loud in the debrief: **students have now written the interesting 90% of an agent framework.**

---

## Answer Key — README Practice Tasks

**Practice 1 (predict).** Typical real run: 2 tool calls in iteration 1 (`get_current_time`, `multiply` — independent, so often parallel), 1 in iteration 2 (`add`, which *needs* multiply's 105), then iteration 3 returns text. Three iterations total. The key insight students must reach: `add` cannot be issued in iteration 1 because its input doesn't exist yet. Dependency, not preference, drives iteration count. Some runs differ — that variance is itself the lesson.

**Practice 2 (label the output).** `--- Iteration N ---` is the loop construct (step 5); `Model requested N tool call(s)` is step 2 (parsing `assistant_message.tool_calls`); `-> name(args)` is step 3 about to dispatch; `<- result` is step 3's return plus step 4's append.

**Practice 3 (history growth).** Before iteration 1: 2 messages (system + user). One iteration with N tool calls adds **1 + N** messages (the assistant turn, then one `tool` message per call). Formula students must state: `1 + N`.

**Practice 4 (infinite loop).** With the tool-result append removed, the model never sees an answer, so it re-requests the same tool every iteration until `MAX_ITERATIONS` stops it. Some models instead give up and answer from memory — also worth discussing: the model *guessed* because you starved it of data.

**Practice 5 (sabotage a description).** With `"Does a thing."` the model usually skips the tool and does the arithmetic itself — which for `15 × 7` looks harmless and is exactly the danger: it will silently do the same on numbers it gets wrong. The description is the *only* signal linking user intent to the tool.

**Practice 6 (`power` tool).** Three edits: function, `TOOL_REGISTRY`, `TOOL_SCHEMAS`. Symptoms of forgetting each: (a) missing function → `KeyError` caught as `ERROR: unknown tool`; (b) missing registry entry → same error, model apologises or falls back; (c) missing schema → the model never calls it at all and does the maths itself. Answer to the task: 2^10 − 24 = **1000**.

**Practice 7 (iteration control).** 1 iteration: `"What is the capital of France?"` (no tool fits). 2 iterations: `"What is 4 + 4?"`. 4+: `"Add 2 and 2, multiply that by 3, subtract 1, then divide by 2"` — each step consumes the previous result, so they cannot be batched.

**Practice 8 (circuit breaker).** Returning a message beats raising because the caller gets a usable, honest result and the partial work isn't lost; raising is better when a silent truncation could be mistaken for a real answer downstream. Accept either position **with a reason** — the point is that students recognise it as a design decision, not a default. The optional timeout is implemented in `loop.py` (`MAX_SECONDS`).

**Practice 9 (error recovery).** The raw `ZeroDivisionError` usually produces a terse "I can't do that." The guided message (`"Cannot divide by zero. Ask the user for a non-zero divisor."`) produces a reply that tells the user what to do next. Line to land: **an error message is a prompt** — write it for the model, not for a stack trace.

---

## Answer Key — Self-Check Questions

1. **Exit condition:** `assistant_message.tool_calls` is empty/None. The model, not the code, decides.
2. **Unknown tool:** `TOOL_REGISTRY[tool_name]` raises `KeyError` → caught → `"ERROR: unknown tool 'x'"` becomes the tool result → appended as a `tool` message → the model reads it next turn and adapts. The loop never crashes.
3. **Growing list:** the model is stateless between calls. The transcript *is* the memory. Send only the latest message and the model loses the tool results and the original question — it would re-request tools it already ran, or answer the wrong question.
4. **The decision lives** in `response.choices[0].message.tool_calls` — a list of objects each with `.id`, `.function.name`, `.function.arguments` (a JSON **string**, not a dict).
5. **Three edits:** function, registry, schema — symptoms listed under Practice 6.

---

## Grading Shortcuts (instructors)

Fast signals when reviewing a student's project:

| Look for | Red flag |
|----------|----------|
| The final total | Off by a rounding step → they applied tax before discount |
| `if tool_name == ...` in the loop | Hardcoded pipeline — they defeated the exercise |
| Tool descriptions | One-word descriptions → they never hit Practice 5's lesson |
| `raise ValueError("bad input")` | Error written for a developer, not for the model |
| `RUNS.md` | `Expected` column filled in after running → no real prediction happened |
| No file in `invoices/` | The side-effecting tool was never wired up |

**Debrief question that separates the top band:** *"Your agent got the right total. Prove it didn't guess."* The only acceptable answer points at the trace and the assertions — not at the number.

---

## Findings From Building This Solution (use them in the debrief)

Every one of these was discovered by actually running the harness, not by reasoning about it. That's the point.

### 0. The stale read — the best bug in this chapter

The SDK build failed case 1 while the from-scratch build passed it. Same prompt, same tools, same dataset.

The SDK build called `get_budget` → `month_total` → **then** `log_expense` → `subtract`. It read the month's total *before* writing the new expense, so the total was stale by 1,500. It then reported `25,000 − 1,500 = 23,500` remaining instead of `16,000`. Every individual tool returned the correct value. The arithmetic was right. The answer was wrong.

Three lessons, all of them worth more than the fix:

1. **Read-then-write ordering is the model's decision, and it will get it wrong.** Nothing in the tool descriptions said the total had to be read after the write. Fixed with an explicit ordering rule in the system prompt.
2. **This is why you run the same eval against both implementations.** A single build would have shipped green. The bug lives in the model's planning, not in either codebase, so it surfaces intermittently — a second implementation is a cheap second sample.
3. **Assert on order only when order is causal.** Most sequences are the model's business and asserting on them punishes good agents (see finding 2). But *read-before-write returns a stale number*, and no correct arithmetic afterwards can repair it. `check_expenses.py` now asserts `log_expense` precedes `month_total`, with a comment explaining the distinction.

Ask students: *"Your agent reported the right number. Would it still be right if the user had already spent something this month?"*

### 1. The guard that didn't guard

`line_total` raises on negative hours. Case 5 still produced a saved invoice: the model normalised `-3` to `3` **before** calling the tool, so the guard never fired. Fixed by adding rule 6 to `SYSTEM_PROMPT` — an instruction at the layer where the decision happens — while keeping the `raise` as defence in depth.

Line to land: **a validation check only protects you if the bad value reaches it, and the model is always upstream of your validation.**

### 2. Over-specified checks fail correct agents

Three of the first-draft assertions failed on *good* behaviour:

| First-draft check | Why it was wrong |
|---|---|
| The reply must contain the word `"negative"` (case 5) | The SDK build said *"I cannot log that expense. Please provide a positive amount."* — correct refusal, scored FAIL. Match the meaning the user needs, not one phrasing. |
| `apply_discount` must not be called *(earlier invoice draft)* | The model called it with `percent=0`. Legitimate. Assert the outcome, not the path. |
| A tool must error on invalid input *(earlier invoice draft)* | The model read the valid values off the tool *description* and refused without spending a call — cheaper and smarter than what we asked for. |
| The reply must contain `"?"` *(earlier invoice draft)* | It asked with a numbered list of required fields. Perfectly good asking. |

Line to land: **assert on outcomes and on what must never happen (no file written, no invented rate), not on the exact sequence of calls.** An eval that punishes an agent for finding a better path is a broken eval — and students will write that eval by default. This is the single most useful thing they can carry into Step 5.

---

## Rate Limits (practical note)

The Gemini free tier allows ~15 requests/minute. One invoice run is 6–8 requests, so two runs back to back will trip a `429`. `loop.py` handles this two ways: `_create_with_retry` backs off exponentially, and `check_invoice.py` pauses 30s between cases. Expect the full 5-case harness to take ~3 minutes. If students report "my agent randomly crashes," it's almost always this.
