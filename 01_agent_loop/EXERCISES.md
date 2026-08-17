# Step 1 — Exercises

> Prerequisite: you have finished **all 9 practice tasks** in `README.md`. These exercises assume you can already add a tool, read the loop output, and explain the exit condition.

Work top to bottom. Difficulty climbs deliberately.

| Tier | Exercises | Time | What it proves |
|------|-----------|------|----------------|
| **Warm-up** | 1–3 | ~35 min | You can read and modify the loop |
| **Guided build** | 4–5 | ~70 min | You can apply the loop to build something new |
| **Challenge** | 6–7 | open-ended | You can design a solution nobody handed you |

**Rules:** work in copies inside `from_scratch/` (`my_agent.py`, `my_tools.py`) so the originals stay clean as a reference. Reference solutions are in `solutions/` — open them only after you've made a real attempt.

**Where these sit in the chapter:** exercises are Layer 3. After them comes `with_sdk/compare.md` (Layer 4 — the same agent on the Agents SDK) and then `PROJECT.md` (Layer 6 — Spendly Lite v1). Exercises 3 and 5 are directly reused by the project, so don't skip them.

---

## Warm-up `[core]` · 1 hr

*Exercises 1–3 are the core path. Everything below them is `[depth]` — genuinely worthwhile, and not required before Chapter 2.*

### Exercise 1 — The `percentage_of` tool ⭐ `[core]`

Add a tool `percentage_of(value, percent)` that returns `percent`% of `value`.

Then run:

```python
run_agent("A laptop costs 85000. Calculate 15% of it, then subtract that from the original price.")
```

**You're done when:**
- [ ] The agent returns `72250`
- [ ] The trace shows `percentage_of` called, then `subtract` called with the result
- [ ] `uv run pyright 01_agent_loop/from_scratch/my_tools.py` reports 0 errors

**Trap to avoid:** if the model does the percentage in its head instead of calling your tool, your `description` is too weak. Fix the description, don't fix the prompt.

---

### Exercise 2 — Change the agent's behaviour with the system prompt only ⭐ `[core]`

Do not touch any tool or loop code. Edit **only** the `system_prompt` string so the agent:

1. Refuses politely to answer anything that isn't a math or time question
2. Always states which tools it used in its final answer
3. Reports all currency amounts in PKR with thousands separators

Test with three inputs: a valid math question, a time question, and `"Write me a poem about Karachi."`

**You're done when:**
- [ ] The poem request is refused, and **zero tools are called** for it (1 iteration only)
- [ ] Valid math questions still work end to end
- [ ] The final answer names the tools used

**Why this matters:** the `system` message is the cheapest, fastest control surface you have. Most "the agent is misbehaving" bugs are system-prompt bugs, not code bugs.

---

### Exercise 3 — Instrument the loop ⭐⭐ `[core]`

> Do not skip this one. The project's acceptance checklist requires the run summary it produces.

Add a run summary printed after the loop finishes:

```
=== RUN SUMMARY ===
Iterations used     : 3 / 10
Tool calls executed : 4
Tool errors         : 1
Tools used          : multiply(2), add(1), divide(1)
Final message length: 214 chars
```

Count these with plain Python counters inside `run_agent`.

**You're done when:**
- [ ] The summary prints on every run, including the `MAX_ITERATIONS` exhaustion path
- [ ] `Tool errors` correctly counts a run of `"divide 10 by 0"` as 1
- [ ] Counters are computed in the loop, not re-derived by re-reading `messages` afterwards

**Forward hook:** you just built the primitive version of *tracing*. Frameworks sell this as an observability dashboard. It's four integers.

---

## Guided Build `[depth]` · 1.5 hrs

### Exercise 4 — The Unit Converter Agent ⭐⭐⭐ `[depth]`

**Time: ~30 min.** Build a new agent in `unit_agent.py` + `unit_tools.py`.

Tools to implement (all pure Python — no API calls):

| Tool | Signature | Notes |
|------|-----------|-------|
| `celsius_to_fahrenheit` | `(celsius: float) -> float` | |
| `km_to_miles` | `(km: float) -> float` | |
| `kg_to_pounds` | `(kg: float) -> float` | |
| `round_number` | `(value: float, decimals: int) -> float` | Forces a second chained call |

Then run this task, which requires **at least three tool calls across at least two iterations**:

> "I'm shipping a 12.5 kg package 340 km, and the warehouse is 31°C. Give me all three values in imperial/Fahrenheit units, each rounded to 1 decimal place."

**You're done when:**
- [ ] `unit_agent.py` runs standalone (`uv run python 01_agent_loop/from_scratch/unit_agent.py`)
- [ ] The trace shows ≥ 3 tool calls
- [ ] At least one `round_number` call takes the *output of another tool* as input — visible in the trace
- [ ] Unknown units (e.g. asking for "gallons") produce a graceful "I don't have a tool for that" answer rather than a hallucinated number
- [ ] `uv run pyright` reports 0 errors on both files

**Design question to answer in a comment before coding:** should `round_number` be a tool at all, or should each converter just round internally? Write your reasoning in two sentences. (There is a defensible answer either way — the point is that *you decided*, on purpose.)

---

### Exercise 5 — Return a structured trace, not just a string ⭐⭐⭐ `[depth]`

**Time: ~40 min.** Right now `run_agent` returns a bare `str`. That's untestable. Change it to return a structured result.

```python
from dataclasses import dataclass, field

@dataclass
class ToolCallRecord:
    name: str
    arguments: dict
    result: str
    errored: bool

@dataclass
class AgentRun:
    final_answer: str
    iterations: int
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    hit_max_iterations: bool = False

    @property
    def tool_names(self) -> list[str]:
        return [tc.name for tc in self.tool_calls]
```

`run_agent` returns an `AgentRun`. The `__main__` block prints `run.final_answer`.

Then — and this is the actual point of the exercise — write **five assertions** in a `check_agent.py` file that verify real behaviour:

```python
run = run_agent("What is 15 times 7?")
assert "multiply" in run.tool_names,        "expected the multiply tool to be used"
assert run.iterations <= 3,                 f"took too many iterations: {run.iterations}"
assert not run.hit_max_iterations,          "should not exhaust the budget"
assert "105" in run.final_answer,           "the answer should contain 105"
assert not any(tc.errored for tc in run.tool_calls), "no tool should have errored"
print("All checks passed.")
```

**You're done when:**
- [ ] `run_agent` returns `AgentRun` and the old print behaviour still works
- [ ] `check_agent.py` runs and prints `All checks passed.`
- [ ] You deliberately break one thing (e.g. rename the `multiply` schema) and watch a specific assertion fail with a readable message
- [ ] `uv run pyright` reports 0 errors

**Why this matters more than it looks:** you just wrote your first agent *eval*. Step 5 builds a full harness with a golden dataset and an LLM judge — but the core idea is exactly this: run the agent, assert on structured facts about what it did, not just what it said. An agent that returns the right answer via the wrong tools is a bug waiting to bite you.

---

## Challenge `[depth]` · 1 hr

> No step-by-step instructions. Design it yourself.

### Exercise 6 — Multi-turn conversation ⭐⭐⭐⭐ `[depth]`

Right now every call to `run_agent` starts from an empty history. Build a **REPL** where the user can chat continuously and the agent remembers everything earlier in the session:

```
You: what's 15 * 7?
Agent: 105
You: now add 23 to that
Agent: 128          <- it must know what "that" refers to
You: /quit
```

Requirements you must satisfy however you see fit:
- Follow-up references like "that", "the previous result", "the number you just gave me" must resolve correctly
- `/quit` exits cleanly; `/reset` clears the history and starts fresh
- After each turn, print the running message count and a rough token estimate (`len(str(messages)) // 4` is fine)

**You're done when:**
- [ ] A 6-turn conversation with at least three back-references resolves correctly
- [ ] You have recorded the message count and token estimate after each turn
- [ ] You can answer: **at what turn count does this design break?** Give a number and the reason.

**This is the hook for Step 3.** Your token estimate grows every turn and never shrinks. Eventually you exceed the context window, the API rejects the request, and your agent dies mid-conversation. Feel that limit now — you'll fix it properly with a context manager next.

---

### Exercise 7 — The human approval gate ⭐⭐⭐⭐⭐ `[depth]`

Add a tool with a **real side effect**: `write_file(filename: str, content: str)`.

Some tools are safe to run automatically (`add`). Some are not (`write_file`, `send_email`, `charge_card`, `delete_record`). Design a mechanism where dangerous tools require explicit human approval **before** execution:

```
  -> write_file({'filename': 'report.txt', 'content': '...'})
  ⚠ APPROVAL REQUIRED — allow this call? [y/N]: n
     <- ERROR: user denied permission to run write_file
```

Constraints:
- Which tools need approval must be **declarative metadata**, not an `if tool_name == "write_file"` buried in the loop
- A denial must be fed back to the model as a tool result so it can respond gracefully — it must not crash the loop
- The agent must handle denial sensibly: acknowledge it, don't silently pretend it succeeded, don't retry the same call in a loop

**You're done when:**
- [ ] Approving writes the real file
- [ ] Denying produces a graceful final answer that tells the user the file was not written
- [ ] Adding a second dangerous tool requires **zero** changes to the loop code — only metadata
- [ ] Denying twice in a row does not cause an infinite retry loop

**Think about:** this is exactly what Claude Code does when it asks you to approve a command, and it's the seed of Step 6's guardrails. The design decision that matters — where does the policy live? — is an architecture question, not a coding one.

---

## Finished?

Two things left in this chapter, in order:

1. **`with_sdk/compare.md`** — the same agent rebuilt on the OpenAI Agents SDK, plus Practices 10 and 11. You've earned the right to use the framework; now find out exactly what it took over.
2. **`PROJECT.md`** — **Spendly Lite v1**, built both ways and graded by one dataset.

Chapter 2 waits until the project's acceptance checklist passes.

> **Note on Exercise 7:** the approval gate you designed is `needs_approval=True` in the Agents SDK — one keyword argument. You'll meet it properly in the trust chapter. Having built it by hand first is why it will look obvious rather than magic.
