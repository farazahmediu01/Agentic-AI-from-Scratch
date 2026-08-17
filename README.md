# Agentic AI From Scratch

Become fluent in the **OpenAI Agents SDK** — by building each mechanism by hand just deeply enough that the framework stops feeling like magic, then shipping real agents with the SDK.

> If a framework solves it in 3 lines, we write the 30 lines underneath so we know what those 3 lines *cost* — **and then we use the 3 lines, forever after.**

## Why This Exists

Most agentic AI tutorials start with `pip install openai-agents` and call it a day. Students learn to *use* a framework but can't explain what happens inside it. When something breaks — and it always breaks — they're stuck.

The opposite mistake is just as bad, and this repo made it first: building everything by hand forever, and never becoming fluent in the tool the industry actually hires for. An early version of Chapter 2 spent 90 minutes rebuilding a schema generator. That's metaprogramming, not agent building.

So the rule now is narrow and explicit:

> **Hand-roll only what you must be able to picture while debugging at 2am. Everything else is SDK from first contact.**

The hand-rolled work gives you **understanding**. The SDK work gives you **framework mastery**. One app that grows all curriculum long, plus an agent of your own choosing, gives you **practical confidence**.

By the end you should be able to say:

> *"I understand what an agent framework does internally, but I don't need to build everything myself. I can confidently use the OpenAI Agents SDK to design, build, evaluate, debug and extend real agentic applications."*

## Who This Is For

- **Instructors** — start with [`INSTRUCTOR.md`](INSTRUCTOR.md), the operating manual for teaching this
- **Students** who want to understand how agents actually work, not just how to call an API
- **Self-learners** building toward production AI agent roles

### Prerequisites — stated honestly

You need **working Python**, not beginner Python: functions, dicts, loops, exceptions, classes, imports, and comfort reading a traceback.

You do **not** need type hints beyond the basics, decorators, dataclasses, Pydantic, `async`/`await`, or pytest — those are **Chapter 0**, which is about 6 hours and opens with a 6-question diagnostic so you can skip the parts you already know. Skip Chapter 0 entirely and you will stall in Chapter 2.

No AI/ML background required.

## The Roadmap

| Ch | What You Build | Axes | Status |
|----|---------------|------|--------|
| 0 | **Python for Agents** — typing, decorators, dataclasses, Pydantic, async, pytest | — | ✅ Built |
| 1 | **The Agent Loop** — the `while` loop every framework wraps | 🧠🔒📐 | ✅ Built |
| 2 | **Typed Tools** — validation before the function body runs | 🔒📐 | ✅ Built |
| 3 | **Structured Outputs** — typed answers, and evals that stop guessing | 📐🧠 | ✅ Built |
| — | *everything below is a hypothesis, not a promise* | | |
| 4 | **Sessions & State** — persistence, context objects as DI | 🧠 | ⬜ Next |
| 5 | **The Context Window** — Chapter 4's failure mode | 🧠 | ⬜ |
| 6 | **Evals** — golden datasets, LLM-as-judge, regression | 📐 | ⬜ |
| 7 | **Specialists** — handoffs, agents-as-tools | 🧠🔒 | ⬜ |
| 8 | **Guardrails & Approvals** | 🔒 | ⬜ |
| 9 | **Observability** — tracing, streaming, cost & token accounting | 📐 | ⬜ |
| 10 | **Serving & MCP** — FastAPI + Model Context Protocol | 🔒📐 | ⬜ |
| 11 | **Hosted Tools & the Responses API** — the one paid chapter (~$5) | 🔒 | ⬜ |
| 12 | **Cold Build Capstone** — unfamiliar domain, no scaffolding | all | ⬜ |

Chapters past the next one are **deliberately not designed yet.** Each is specified only once the previous is built and validated, so the sequence stays coherent instead of aspirational.

**Two decisions worth noticing.** Evals sit in the *middle*, not at the end — from Chapter 6 on, "the eval suite is still green" is an acceptance criterion for every later chapter, which is what turns a growing project into a compounding one. And Chapter 12 is a cold build in a domain you've never worked in, because it's the only assessment that can tell "learned it" apart from "copied it."

Every chapter but the paid one runs **free**, on Gemini's OpenAI-compatible endpoint. Why that choice and what it costs: [`RESPONSES_VS_CHATCOMPLETIONS.md`](RESPONSES_VS_CHATCOMPLETIONS.md).

## The Three Tracks

Every chapter ships all three. They exist because doing forty tasks in one domain teaches you that domain, not the concept.

| Track | What | Domain | Graded on |
|---|---|---|---|
| 1️⃣ **Drills** | Small, disposable SDK reps, 10–20 min each | Rotating throwaway — dice, timers, fake weather, trivia. **Never expenses** | Does it run |
| 2️⃣ **The Spine** | **Spendly Lite** — one expense assistant, extended every chapter. Locked spec, locked seed data | Expenses, always | Its golden dataset — **plus every earlier chapter's cases still passing** |
| 3️⃣ **Your Own Agent** | Your domain, your choice, picked in Chapter 1 and extended every chapter after. SDK-only, blank file, no scaffolding | Yours | **Evidence, not features** — 3 logged runs + what broke + what you changed |

Track 3 is the one that matters most for your portfolio, and it's graded the same way in every chapter:

```
[ ] The chapter's capability works in YOUR agent
[ ] RUNS.md has 3 new runs, dated, with real output pasted in
[ ] One paragraph: what broke, what you changed
[ ] It is not an expense tracker
```

An agent that broke, with the breakage documented, passes. A working agent with no runs does not.

## Time Budgets — real numbers

Every chapter header carries **two** numbers, and every section is marked `[core]` or `[depth]`:

- **Core** — the critical path. Finish this and you're ready for the next chapter.
- **Full** — core plus every depth section, challenge and optional drill.

A chapter is **2–3 sessions**, not one. If a header's number disagrees with the sum of its own task estimates, the header is a bug — report it.

## Stack

| Tool | Role |
|------|------|
| Python 3.12+ | Language |
| [uv](https://docs.astral.sh/uv/) | Package manager (replaces pip + venv) |
| **openai-agents** | **The destination** — the SDK you're here to master |
| OpenAI Python SDK | Transport layer for the hand-rolled spikes |
| Gemini (free tier) | LLM provider via OpenAI-compatible endpoint — zero cost |
| pydantic | The validation layer — tool contracts are Pydantic models from Chapter 2 on |
| ruff | Formatter + linter in one binary |
| pyright | Static type checker |
| pytest | Boundary tests — no API key, milliseconds |

### The quality gate

Every chapter passes all four before it ships. A teaching repo has no excuse for a lower bar than a production one — students copy what they see.

```powershell
uv run ruff format .     # style
uv run ruff check .      # lint
uv run pyright           # types
uv run pytest            # proof
```

**The framework rule is scoped, not absolute.** In a `spike/` folder no agent framework is allowed and the OpenAI SDK is a transport layer only — but a spike over ~60 lines is a design failure, not a thorough lesson. In `with_sdk/` the Agents SDK is used as intended, and re-implementing what it provides defeats the point. No LangChain, LlamaIndex or Haystack anywhere.

## The Three Axes

Every concept is tagged with the kind of problem it solves — a diagnostic you carry into real debugging:

| Axis | Question | Examples |
|---|---|---|
| 🧠 **State** | What does it remember? | the message list, context window, sessions |
| 🔒 **Trust** | What is it allowed to do? | tools as permissions, turn limits, guardrails, approvals |
| 📐 **Proof** | How do we know it worked? | golden datasets, run evidence, traces, evals |

## Quick Start

### 1. Clone and install

```bash
git clone https://github.com/farazahmediu01/Agentic-AI-from-Scratch.git
cd Agentic-AI-from-Scratch
uv sync
```

### 2. Set up your API key

Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey), then:

```bash
cp .env.example .env
# Open .env and paste your Gemini API key
```

### 3. Run the agent

```bash
uv run python 01_agent_loop/from_scratch/agent.py
```

You should see the agent loop in action — the model deciding which tools to call, chaining results across turns, and producing a final answer:

```
--- Iteration 1 ---
Model requested 2 tool call(s):
  -> get_current_time({})
     <- 2026-06-23T14:08:11
  -> multiply({'a': 15, 'b': 7})
     <- 105

--- Iteration 2 ---
Model requested 1 tool call(s):
  -> add({'a': 105, 'b': 23})
     <- 128

--- Iteration 3 ---
Model returned a final answer — exiting loop.
```

### 4. Type check

```bash
uv run pyright 01_agent_loop/
```

Target: 0 errors before moving on.

## How Each Chapter Is Structured

### The core principle: you never read for long without building

Reading and watching don't stick. So **no concept is taught without a hands-on task attached to it**:

```
CONCEPT → PRACTICE → (CHALLENGE) → ... per section ... → CHAPTER PROJECT
```

Practice tasks live **inline, directly under the concept they teach** — not batched at the end. Each is small, completable in 5–15 minutes, and ends with an explicit *"You're done when..."*.

Difficulty climbs: read → edit → extend → **design from a blank file**. That last rung is the one most curricula skip. Recognition, recall and generation are three different skills, and only the third is fluency — so **every chapter contains at least one task that starts from an empty file with no scaffolding.**

### The six layers

| Layer | Where | What |
|---|---|---|
| 1 Concept | `README.md` | The mechanism, mental model first, a practice task under each concept |
| 2 Spike | `spike/` | The mechanism by hand — **only where it earns its place** |
| 3 Practice | inline + `EXERCISES.md` | Track 1 drills. Predict, run, break, extend |
| 4 SDK | `with_sdk/` | The capability on the OpenAI Agents SDK, plus `compare.md` |
| 5 Bridge | `SDK_BRIDGE.md` | Our code → SDK abstraction → what it does for us |
| 6 Project | `PROJECT.md` | Track 2 spine increment + Track 3 own-agent increment |

**Layer 4 is the destination. Layer 2 is optional** — most later chapters have no hand-rolled layer at all, and that's correct.

### Build-twice has an expiry date

Chapters 1 and 2 build the spine twice — once by hand, once on the SDK — graded by one golden dataset. That's genuinely useful early: the second implementation doubles as a second behavioural sample of a non-deterministic system.

From Chapter 3 the spine goes **SDK-only** and the hand-rolled layer becomes a disposable 40–60 line spike, deleted after the chapter. Doubling the whole app forever is O(n²) and would collapse a few chapters in.

The rule for when doubling is worth it: **build twice when the hand-rolled version is correct-but-verbose, and not at all when it is simply worse.** Chapter 1's loop and Chapter 2's validation were the first kind. Chapter 3's prompt-and-parse is the second — the chapter spends 25 minutes proving it can't be made reliable, so shipping the app on it would teach a practice we'd just disproved.

### Every chapter produces evidence

Both project tracks require a `RUNS.md`: test cases with *expected* outputs written down **before** running, and actual results after. That's a golden dataset built by hand in Chapter 1 — so by the time Chapter 6 automates it, the idea is already a habit rather than framework magic.

## For Instructors

**Plan 2–3 sessions of 90–120 minutes per chapter.** Check each chapter's Core/Full budget first.

| Phase | Duration | Activity |
|-------|----------|----------|
| Concept + inline practice | 40–50 min | Teach one concept, students immediately do the task under it, repeat. Never more than ~8 minutes of talking before they type something. |
| Drills | 30–40 min | Track 1. Instructor circulates. |
| Debrief | 10–15 min | Review. Discuss what broke. Name the limitation this chapter can't solve — that's the hook for next time. |
| Project | Lab / homework | Track 2 + Track 3 increments, both with `RUNS.md`. |

**Key teaching moves:**
- Start with the mental model, not the code. Ask students to predict.
- Run before reading. Let students see the output, then trace backward.
- Let exercises fail. Students hitting real bugs *is* the learning.
- Skip the `[depth]` blocks in class. They're for students who want them, not for the session plan.
- End every session by naming what the current chapter can't do.

## What You'll Be Able To Do

- Open a blank file and write a working, tool-using, evaluated SDK agent **unaided**
- Explain what the SDK is doing underneath any abstraction you use
- Debug emergent agent failures — a dropped handoff, a context overflow, a guardrail fighting a four-chapter-old system prompt
- Prove an agent works with a golden dataset and a regression suite
- Decide when a framework is the right call and when it isn't

## License

MIT

## Author

**Faraz Ahmed** — Python & Web Dev Educator | Building toward Senior Agentic AI Engineer

- GitHub: [@farazahmediu01](https://github.com/farazahmediu01)
- LinkedIn: [Faraz Ahmed](https://www.linkedin.com/in/faraz-ahmed-01/)
