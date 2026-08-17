# Chapter 1 — The Agent Loop

> The single most important pattern in agentic AI. Every framework you've ever heard of — OpenAI Agents SDK, Claude Agent SDK, LangChain, AutoGen, CrewAI — is a different opinion on top of *this* loop.

**Axes:** 🧠 State (the message list *is* the agent's memory) · 🔒 Trust (tools are permissions; limits are circuit breakers) · 📐 Proof (a golden dataset that outlives your implementation)

| Part | Core | Full |
|---|---|---|
| This README — 9 concepts, each with a practice | 2.75 hrs | 3 hrs |
| [`EXERCISES.md`](EXERCISES.md) — Track 1️⃣ drills | 1 hr | 3.5 hrs |
| [`PROJECT.md`](PROJECT.md) — Tracks 2️⃣ + 3️⃣ | 4.5 hrs | 5 hrs |
| **Chapter total** | **≈ 8 hrs** | **≈ 11.5 hrs** |

**Plan 2–3 sessions.** Roughly 150 model calls on the free tier.

> **The old header said "~4 hrs" for all of it.** That was wrong — adding up this chapter's own per-task estimates gives 10–11. If you were pacing yourself against the old number and feeling slow, you weren't; the number was. Finish the **core** column and you can start Chapter 2 with nothing missing.

---

## How to Use This Chapter

**Read a concept → do the practice task under it → move on.** Do not read the whole file and then go back for the tasks. The tasks are what make the concept stick.

Every chapter in this curriculum has six layers. Do them in order:

| Layer | Where | What |
|---|---|---|
| 1 Concept | this README | The mechanism, taught plainly |
| 2 From scratch | `from_scratch/` | You build the mechanism by hand |
| 3 Practice | inline + `EXERCISES.md` | Track 1️⃣ drills — predict, run, break, extend |
| 4 SDK | `with_sdk/` | The same thing with the OpenAI Agents SDK — **the destination** |
| 5 Bridge | `../SDK_BRIDGE.md` | Our code → SDK abstraction → what it does for us |
| 6 Project | `PROJECT.md` | Track 2️⃣ **Spendly Lite** + Track 3️⃣ **your own agent** |

> **Chapter 1 hand-rolls more than any later chapter, on purpose.** The loop, the message array and the tool-call JSON are the three things you must be able to picture while debugging at 2am, so you build all three by hand here. From Chapter 2 on, the hand-rolled layer shrinks fast and the SDK layer grows. By Chapter 4 the app is SDK-only.

Reference solutions are in `solutions/`. **Open them only after attempting.** Looking first feels efficient and teaches nothing.

### Setup check (do this now)

```powershell
cd C:\Users\Faraz\Desktop\agentic-ai-from-scratch
uv sync
copy .env.example .env    # then paste your free Gemini key into .env
uv run python 01_agent_loop/from_scratch/agent.py
```

You're ready when the script prints iterations and a final answer. If it errors on a missing key, your `.env` isn't filled in.

### 3️⃣ Pick your own agent's domain — do this before you read further (10 min)

You will build **three** things across this curriculum, and one of them is entirely yours.

| Track | What | Domain |
|---|---|---|
| 1️⃣ Drills | Small disposable exercises | Ours, rotating — dice, timers, converters |
| 2️⃣ The Spine | Spendly Lite, the app that grows every chapter | Expenses, fixed |
| 3️⃣ **Your Own Agent** | **Yours.** Starts here, gains a capability every chapter | **You choose, now** |

Track 3 is the one that ends up in your portfolio, and it is the only one where nobody hands you a spec. Pick a domain you actually care about and know something about — that knowledge is the scarce ingredient, not the code.

Good picks look like: a recipe planner, a workout logger, a D&D session companion, a study-schedule builder, a plant-care assistant, a fantasy-league helper.

**Two rules:**

- **It must not be an expense tracker.** That's the spine's job, and the whole point of a second domain is that you can't pattern-match your way through it.
- **It must have at least three things worth doing** — the tools you'll add in Chapter 2 need somewhere to live.

Write it down now, in one sentence, in a new file `my_agent/README.md`:

> *"My agent helps ______ do ______ by ______."*

**You're done when:** that file exists and the sentence is specific enough that someone else could tell whether your agent worked.

> **Expect rate limits.** The Gemini free tier allows about **15 requests per minute**, and one agent run is 6–8 requests. Two runs back to back can return `429 RESOURCE_EXHAUSTED`. That is not a bug in your code — wait a minute and re-run. (`solutions/loop.py` shows how to retry with exponential backoff.)

---

> ### On `[core]` and `[depth]` in this chapter
>
> Later chapters mark sections `[core]` (the critical path) and `[depth]` (skippable on a first pass). **Chapter 1 is almost entirely core**, and that is not laziness in the marking — it is what a foundation chapter looks like. All nine concepts below are the loop, and you cannot skip part of the loop.
>
> Chapter 1's depth lives in two places: the guided builds and challenges in [`EXERCISES.md`](EXERCISES.md), and the second (SDK) build of the project. Those are where the optional hours are.

---

## Concept 1 — The Mental Model: A Restaurant Kitchen  🧠 `[core]` · 15 min

Imagine a head chef who can read recipes and decide what to cook, but **cannot physically touch anything** in the kitchen. They have cooks they can shout to:

- A **clock cook** who tells them the current time
- An **addition cook** who adds two numbers
- A **multiplication cook** who multiplies two numbers

The chef gets an order, *thinks* about which cook to call, *shouts the request*, the cook does it and *shouts the result back*, the chef *thinks again*, and so on. When the chef has everything they need, they call "**plate up**" — that's the final answer to the customer.

| Kitchen | Agentic loop |
|---|---|
| Order arrives | User message |
| Chef thinks | LLM API call |
| Chef shouts "I need X!" | Tool call in model response |
| Cook does it, shouts result | Tool function executes, result captured |
| Chef sees result, thinks again | Result appended to conversation, next API call |
| "Plate up" — done | Model responds with no tool call → final answer |

The chef is the LLM. The cooks are tools. The shouting back and forth is the loop.

**The loop is just `while not done: think → act → observe`.**

The critical thing to internalise: **the LLM never runs anything.** It only ever produces text. When it "calls a tool," it emits a structured request — a name and some arguments — then *stops and waits*. Your Python code runs the function. The model is a decision-maker, not an executor.

### 🔨 Practice 1 — Predict before you run (5 min)

On paper or in a comment block, **before running anything**. For this task:

> "What's the current time? Also, calculate 15 multiplied by 7, then add 23 to that result."

1. How many tools will the model call in total?
2. In what order?
3. How many round-trips to the model (iterations) will it take?
4. Which tool call *cannot* happen until another finishes first, and why?

**Confidence, 1–5:** ___

Now run `uv run python 01_agent_loop/from_scratch/agent.py` and compare.

<details>
<summary><b>Open only after you've written your prediction</b></summary>

Typical run: 2 calls in iteration 1 (`get_current_time`, `multiply` — independent, so often issued together), 1 in iteration 2 (`add`, which *needs* multiply's 105), then iteration 3 returns text. **Three iterations.**

The insight: `add` cannot be issued in iteration 1 because its input doesn't exist yet. **Dependency, not preference, drives iteration count.** Your run may differ — that variance is itself the lesson.

</details>

**You're done when** you have written predictions and can name one place reality differed — or explain why it matched exactly.

> **Why this matters:** if you can't predict an agent's behaviour, you can't debug it. Prediction-first is how you build the model that makes production incidents legible.

---

## Concept 2 — The Five Steps in Code  🧠 `[core]` · 20 min

```
1. Send the conversation so far to the LLM.       <- chat.completions.create(...)
2. Parse the model's response.                    <- response.choices[0].message
3. If the response is a tool call, execute it.    <- TOOL_REGISTRY[name](**args)
4. Append the tool result to the conversation.    <- messages.append({"role": "tool", ...})
5. Go to step 1.                                  <- for-loop iteration
```

Everything a framework adds — handoffs, sessions, guardrails, tracing — is scaffolding around these five lines of intent.

| File | Purpose |
|------|---------|
| `from_scratch/tools.py` | Five trivial tools + their JSON schemas + the dispatch registry |
| `from_scratch/agent.py` | The agent loop itself — ~80 lines of real code |

### 🔨 Practice 2 — Label the output (10 min)

Run the agent and copy its output into a scratch file. Annotate **every printed line** with which of the five steps produced it:

```
--- Iteration 1 ---              <- STEP 5 (loop iteration begins)
Model requested 2 tool call(s):  <- STEP 2 (we parsed tool_calls from the response)
  -> get_current_time({})        <- STEP 3 (about to execute)
     <- 2026-06-23T14:08:11      <- STEP 3 (result captured) + STEP 4 (appended)
```

Then find the exact line number in `agent.py` that printed each one.

**You're done when** every printed line has a step number *and* a line number next to it.

---

## Concept 3 — The Conversation Is Just a List of Dicts  🧠 `[core]` · 20 min

There is no hidden state. No session object. No memory system. The agent's entire "mind" is this:

```python
messages: list[ChatCompletionMessageParam] = []
messages.append({"role": "system",  "content": system_prompt})
messages.append({"role": "user",    "content": user_message})
# ... later ...
messages.append(assistant_message)                                     # what the model said
messages.append({"role": "tool", "tool_call_id": ..., "content": ...}) # what the tool returned
```

Every turn, **the whole list** is sent again. The model is stateless — it remembers nothing between API calls. The illusion of memory is just you re-sending the transcript.

| Role | Who wrote it | Purpose |
|------|-------------|---------|
| `system` | You | Standing instructions — persona, rules, behaviour |
| `user` | The human | The request |
| `assistant` | The model | Its reply — text, or tool calls, or both |
| `tool` | Your code | The output of a tool the assistant asked for |

The `tool` message links back to the assistant's request via `tool_call_id`. That's the wiring that tells the model *which* request a result answers when it asked for three tools at once.

### 🔨 Practice 3 — Watch the conversation grow (10 min)

Add this inside the loop in `agent.py`, right after the iteration banner:

```python
print(f"    [history: {len(messages)} messages -> {[m['role'] for m in messages]}]")
```

Predict first, then run. **Confidence, 1–5:** ___

1. How many messages exist before iteration 1's API call?
2. How many are added per iteration when the model calls two tools?
3. What's the final length?

<details>
<summary><b>Open after you predict</b></summary>

Before iteration 1: **2** (system + user). One iteration with N tool calls adds **1 + N** messages — the assistant turn, then one `tool` message per call.

</details>

**You're done when** you can state the formula: *"one iteration with N tool calls adds ___ messages."*

> **Forward hook:** this list only grows. Never shrinks. That's a bill you pay in tokens on every turn — the exact problem the context-management chapter solves.

---

## Concept 4 — Breaking It On Purpose  🧠 `[core]` · 15 min

The fastest way to understand why a line exists is to delete it and watch the failure.

The loop's most load-bearing line appends the tool result. Without it the model asks for a tool, gets no answer, and — reasonably — asks again. Forever.

### 🔨 Practice 4 — Cause the infinite loop (10 min)

1. Comment out the `messages.append({...})` block with `"role": "tool"`.
2. Run the agent. Watch all 10 iterations.
3. **Uncomment it.**

Then: **what stopped the agent from running forever?** Name the exact variable.

<details>
<summary><b>Open after you've run it</b></summary>

`MAX_ITERATIONS`. Without a tool result the model never sees an answer, so it re-requests the same tool every iteration until the ceiling stops it.

Some models instead give up and answer from memory — also worth noticing: the model **guessed**, because you starved it of data.

</details>

> ⚠️ This burns ~10 API calls. Fine on the free tier. On a paid model with a big context, this exact bug is how people wake up to a $400 invoice.

### ✓ Checkpoint 1 — the loop is yours

You can now state what makes the loop run, what makes it stop, and what happens when its memory is broken. Everything after this point is about *what you put inside* the loop. Safe place to end a session.

---

## Concept 5 — How the Model Sees a Tool: The Schema  🔒 `[core]` · 20 min

The model never sees your Python. It only sees the JSON schema:

```python
{
    "type": "function",
    "function": {
        "name": "multiply",
        "description": "Multiply two numbers and return their product.",
        "parameters": {
            "type": "object",
            "properties": {
                "a": {"type": "number", "description": "First number"},
                "b": {"type": "number", "description": "Second number"},
            },
            "required": ["a", "b"],
        },
    },
}
```

| Field | What it does |
|-------|-------------|
| `name` | The string the model emits. Your registry key must match exactly. |
| `description` | **The most important field in agentic AI.** The only thing telling the model *when* to reach for this tool. |
| `parameters` | JSON Schema of the arguments. The model fills these in. |

Prompt engineering for agents is mostly **tool-description engineering**. A vague description means the model won't use the tool, or will use it at the wrong moment.

A tool is also the unit of **permission**: the set of tools you pass is exactly the set of things your agent is allowed to do. That's why this concept is tagged Trust, not State.

### 🔨 Practice 5 — Sabotage a description (10 min)

Change `multiply`'s description to `"Does a thing."` and run. Then try progressively better ones:

| Description | Did the model call it? |
|---|---|
| `"Does a thing."` | ? |
| `"Multiplies."` | ? |
| `"Multiply two numbers and return their product."` | ? |

Restore the good one when finished.

**You're done when** you have seen at least one run where the model skipped `multiply` (doing the arithmetic in its head instead) and can explain in one sentence why.

> That silent fallback is the danger: on `15 × 7` it looks harmless, and it will do the same thing on numbers it gets wrong.

---

## Concept 6 — The Registry: From String to Function  🔒 `[core]` · 25 min

The model sends back the *string* `"multiply"`. Something must turn that into a Python call:

```python
TOOL_REGISTRY: dict[str, Callable] = {"multiply": multiply, ...}

tool_fn = TOOL_REGISTRY[tool_name]     # string -> function
tool_result = tool_fn(**tool_args)     # dict -> keyword arguments
```

**Adding a tool is always three edits**, and forgetting one is the most common beginner bug:

1. Write the Python function.
2. Add it to `TOOL_REGISTRY` — or the call hits `ERROR: unknown tool`.
3. Add its schema to `TOOL_SCHEMAS` — or the model never knows it exists.

### 🔨 Practice 6 — Add a `power` tool (15 min)

Add a tool raising `a` to the power of `b`. All three edits. Then run:

```python
run_agent("What is 2 to the power of 10, minus 24?")
```

Then break it deliberately: **delete only the registry entry**, keep the schema, run again. Read the error the model receives, and how it responds.

**You're done when:**
- [ ] The agent answers `1000`
- [ ] The trace shows `power` and `subtract` both called
- [ ] You've seen `ERROR: unknown tool 'power'` and can describe what the model did next

---

## Concept 7 — The Exit Condition  🧠 `[core]` · 15 min

Nothing in your code decides when the agent is finished. **The model does.**

```python
if not assistant_message.tool_calls:
    return assistant_message.content or ""
```

A response with no tool calls means "I'm done." That's the whole termination protocol. This is what separates an *agent* from a *pipeline*: a pipeline has a fixed number of steps you wrote; an agent decides its own step count at runtime.

### 🔨 Practice 7 — Control the iteration count with words alone (10 min)

Without touching any code except the task string, produce runs terminating in:

- **exactly 1 iteration** (zero tool calls)
- **exactly 2 iterations** (one round of tools, then the answer)
- **4 or more iterations** (each step needs the previous result)

Record the three task strings.

<details>
<summary><b>Open after you have all three</b></summary>

1 iteration: `"What is the capital of France?"` — no tool fits.
2 iterations: `"What is 4 + 4?"`.
4+: `"Add 2 and 2, multiply that by 3, subtract 1, then divide by 2"` — each step consumes the previous result, so they cannot be batched.

</details>

---

## Concept 8 — The Circuit Breaker  🔒 `[core]` · 10 min

```python
MAX_ITERATIONS = 10
```

Production discipline rule #1: **never let an agent loop run forever.** A confused model plus a buggy tool burns real money fast, and "the model will surely stop eventually" is not an engineering argument.

Note what happens at the ceiling: we don't crash, we return an honest message saying the budget ran out. An agent that fails loudly and truthfully is worth more than one that fails silently.

### 🔨 Practice 8 — Hit the ceiling deliberately (5 min)

Set `MAX_ITERATIONS = 1`, run a chained task, observe the returned message. Then argue both sides in two sentences: is returning a message better or worse than raising an exception? Restore `10`.

<details>
<summary><b>Open after you've taken a position</b></summary>

**Message:** the caller gets a usable, honest result and partial work isn't lost.
**Exception:** a silent truncation can't be mistaken downstream for a real answer.

Either is defensible **with a reason** — the point is recognising it as a design decision, not a default. (The SDK chooses to raise: `max_turns` throws `MaxTurnsExceeded`.)

</details>

> **Challenge (+10 min):** iteration count is a crude budget. Add a *second* ceiling — a wall-clock timeout using `time.monotonic()`. Whichever trips first ends the loop, and the message says which.

---

## Concept 9 — A Tool Crash Must Not Kill the Agent  🔒 `[core]` · 20 min

```python
try:
    tool_result = tool_fn(**tool_args)
except Exception as exc:
    result_str = f"ERROR: {type(exc).__name__}: {exc}"
```

We don't re-raise. The error text becomes the tool's *result* and goes back into the conversation. The model reads it and decides what to do — retry with different arguments, try another tool, or tell the user it can't proceed.

This is a deep idea: **errors are information for the model, not just for the developer.** A well-written error message is a prompt. `"ERROR: ZeroDivisionError: division by zero"` teaches the model something actionable. `"ERROR: something went wrong"` does not.

### 🔨 Practice 9 — Make the agent recover (15 min)

1. Run `run_agent("What is 10 divided by 0?")`. Watch the error flow back.
2. Improve the tool: `raise ValueError("Cannot divide by zero. Ask the user for a non-zero divisor.")`
3. Run again and compare final answer quality.

**You're done when** you can show both final answers side by side and say which serves the user better and why.

> **Challenge (+15 min):** add a `MAX_TOOL_ERRORS` counter — 3 failures in one run ends the loop with a failure summary. Your first hand-rolled guardrail.

### ✓ Checkpoint 2 — your agent survives failure

You can build a loop, give it capabilities, bound its cost, and keep it alive through bad input. That is a complete agent. Everything from here makes it *better*, not *possible*.

---

## What to Notice Overall

1. **The model picked the tools, not you.** No `if/else` says "if the user mentions time, call `get_current_time`."
2. **The model chained tool calls.** `multiply` produced `105`; the next turn fed it to `add`, carried across turns by reading history.
3. **Sometimes it calls multiple tools per turn** (parallel), sometimes one at a time. Its choice, and it varies run to run.
4. **The loop exits on its own.** Nothing says "now stop."

## Production Discipline Already Baked In

| Rule | Where it lives |
|------|----------------|
| Never let the loop run forever | `MAX_ITERATIONS = 10` |
| A tool crash must not kill the agent | `try/except` around the dispatch |
| API keys never in source | `.env` + `load_dotenv()` |

---

## Self-Check Before Moving On

Answer without re-reading the code:

1. What exactly makes the loop *exit*?
2. If the model requests a tool not in `TOOL_REGISTRY`, what happens? Trace it.
3. The `messages` list grows every iteration. Why is that necessary?
4. Where does the model's "decision" physically live in the API response object?
5. Adding a tool takes three edits. Name all three and the symptom of forgetting each.

## Common Pitfalls

- **"My loop runs forever."** You forgot to append the tool result. (Practice 4.)
- **"The API rejects my next turn."** The assistant message with `tool_calls` wasn't preserved exactly, or `tool_call_id` doesn't match.
- **"The model ignores my tools."** The description is too vague. (Practice 5.)
- **"`TypeError: unexpected keyword argument`."** Your schema's `properties` don't match your function's parameter names.

---

## Next — in this order

| Step | File | What |
|---|---|---|
| 1 | `EXERCISES.md` | 3 warm-ups, 2 guided builds, 2 challenges |
| 2 | `with_sdk/compare.md` | **The same agent on the OpenAI Agents SDK** — Practices 10 & 11 |
| 3 | `PROJECT.md` | **Spendly Lite v1** — built twice, graded once |

Do not move to Chapter 2 until the project's acceptance checklist passes. The loop is small enough that you should **own** it before we add anything on top.
