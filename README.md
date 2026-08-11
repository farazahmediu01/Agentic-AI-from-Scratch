# Agentic AI From Scratch

Learn the **OpenAI Agents SDK** properly — by building each mechanism by hand first, then using the SDK to do the same job, then shipping both in one growing app.

> If a framework solves it in 3 lines, we write the 30 lines underneath so we know what those 3 lines *cost* — **and then we use the 3 lines.**

## Why This Exists

Most agentic AI tutorials start with `pip install openai-agents` and call it a day. Students learn to *use* a framework but can't explain what happens inside it. When something breaks — and it always breaks — they're stuck.

The opposite mistake is just as bad: building everything from scratch forever, and never becoming fluent in the tool the industry actually hires for.

So every chapter does both. You build the mechanism by hand, feel exactly what it costs, then implement the same capability with the OpenAI Agents SDK and compare them line by line. The from-scratch work gives you **understanding**; the SDK work gives you **framework mastery**; one app that grows all curriculum long gives you **practical confidence**.

By the end you should be able to say:

> *"I understand what an agent framework does internally, but I don't need to build everything myself. I can confidently use the OpenAI Agents SDK to design, build, evaluate, debug and extend real agentic applications."*

## Who This Is For

- **Instructors** looking for a structured, hands-on curriculum for teaching agentic AI fundamentals
- **Students** who want to understand how agents actually work, not just how to call an API
- **Self-learners** building toward production AI agent roles

**Prerequisites:** Basic Python (functions, dicts, loops, exceptions). No AI/ML background required.

## The Roadmap

Each chapter teaches one mechanism, builds it by hand, rebuilds it with the SDK, and grows Spendly Lite.

| Ch | What You Build | Axes | Folder | Status |
|----|---------------|------|--------|--------|
| 1 | **The Agent Loop** — the `while` loop every framework wraps | 🧠🔒📐 | `01_agent_loop/` | ✅ Complete |
| 2 | **Typed Tools** — schemas from type hints, validation before the body runs | 🔒 | `02_typed_tools/` | Next |
| — | *Structured outputs · context objects · memory & sessions · context window · specialists & handoffs · guardrails & approvals · observability · evals* | | | Provisional |

Chapters beyond 2 are **deliberately not designed yet.** Each is specified only once the previous one is built and validated, so the sequence stays coherent instead of aspirational. See `references/agent-factory-map.md` for the concept checklist they're drawn from.

## Stack

| Tool | Role |
|------|------|
| Python 3.12+ | Language |
| [uv](https://docs.astral.sh/uv/) | Package manager (replaces pip + venv) |
| OpenAI Python SDK | Transport layer to the model — nothing more |
| Gemini (free tier) | LLM provider via OpenAI-compatible endpoint — zero cost |
| pyright | Static type checker |

**The framework rule is scoped, not absolute.** In `from_scratch/` no agent framework is allowed — the OpenAI SDK is a transport layer and every loop, tool, memory system, eval and guardrail is hand-rolled. In `with_sdk/` the OpenAI Agents SDK is used as intended, and re-implementing what it provides defeats the point. No LangChain, no LlamaIndex, no Haystack anywhere.

## The Three Axes

Every concept is tagged with the kind of problem it solves — a diagnostic students carry into real debugging:

| Axis | Question | Examples |
|---|---|---|
| 🧠 **State** | What does it remember? | the message list, context window, sessions |
| 🔒 **Trust** | What is it allowed to do? | tools as permissions, turn limits, guardrails, approvals |
| 📐 **Proof** | How do we know it worked? | golden datasets, run evidence, traces, evals |

## The Project: Spendly Lite

One app, built in Chapter 1 and extended in every chapter after — a personal expense assistant that logs spending and answers questions about it. Students never start a new unrelated project; complexity grows and the codebase is continuous.

Chapter 1 builds it **twice** — once by hand, once on the Agents SDK — and grades both with the same five-case golden dataset. Same verdict, one fifth the code.

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

Target: 0 errors before moving to the next step.

## How Each Step Is Structured

### The core principle: you never read for long without building

Reading and watching don't stick. A student who only reads a chapter forgets it before the next one and arrives unable to build. So in this curriculum **no concept is taught without a hands-on task attached to it**:

```
CONCEPT → PRACTICE → (CHALLENGE) → ... per section ... → CHAPTER PROJECT
```

Practice tasks live **inline in the README, directly under the concept they teach** — not batched at the end. Each one is small, self-contained, completable in 5–15 minutes, and ends with an explicit *"You're done when..."*. Difficulty climbs across a chapter: read → edit → extend → design.

### The six layers

Every chapter has all six, in this order:

| Layer | Where | What |
|---|---|---|
| 1 Concept | `README.md` | The mechanism, mental model first, with a practice task under each concept |
| 2 From scratch | `from_scratch/` | You build the mechanism by hand |
| 3 Practice | inline + `EXERCISES.md` | Predict, run, break, extend |
| 4 SDK | `with_sdk/` | The same capability on the OpenAI Agents SDK, plus `compare.md` |
| 5 Bridge | `SDK_BRIDGE.md` | Our code → SDK abstraction → what it does for us (grows every chapter) |
| 6 Project | `PROJECT.md` | Spendly Lite gains one capability |

**Layer 4 is not optional.** A chapter that stops at the hand-rolled version has failed its purpose.

### Exercise tiers

1. **Warm-up** — modify the existing code (e.g., add a new tool). Proves the student can read and edit the implementation.
2. **Guided build** — apply the step's concepts to build something new and useful. Includes clear acceptance criteria.
3. **Challenge** — an open-ended problem with no step-by-step instructions. Forces the student to design the solution themselves.

Exercises build toward a real agent, not a toy. The warm-up adds a tool. The guided build creates a mini-agent for a real task. The challenge exposes a limitation that the next step solves.

### Every chapter ends with a project

Not a summary — a build. And always the same app: **Spendly Lite** gains one capability per chapter. Chapter 1 gives it a loop and tools, so it can log an expense and report a budget.

Each project also requires a `RUNS.md`: five hand-written test cases with *expected* outputs filled in before running, and actual results after. That's a golden dataset built by hand in Chapter 1 — so by the time the evals chapter automates it, the idea is already a habit rather than framework magic.

## For Instructors

Each step is designed for a **90–120 minute session**:

| Phase | Duration | Activity |
|-------|----------|----------|
| Concept + inline practice | 40–50 min | Teach one concept, students immediately do the practice task under it, repeat. Never more than ~8 minutes of talking before they type something. |
| Exercises | 45–60 min | Students work through warm-up and guided build. Instructor circulates. |
| Debrief | 10–15 min | Review solutions. Discuss what broke. Preview the next step. |
| Project | Homework / lab | The chapter project + `RUNS.md`. Graded against the acceptance checklist in `PROJECT.md`. |

**Key teaching moves:**
- Start with the mental model, not the code. Ask students to predict what the code should do.
- Run before reading. Let students see the output, then trace backward.
- Let exercises fail. Students hitting real bugs is the learning.
- At the end of every session, name the limitation the current step can't solve. That's the hook for next time.

## What You'll Understand After This

After completing all 6 steps, you will be able to:

- Explain how the agent loop works inside any production framework
- Build a working agent from scratch with tool use, memory, and safety guardrails
- Read the source code of OpenAI Agents SDK or Claude Agent SDK and understand every design choice
- Evaluate whether an agent's output is correct using a hand-built eval harness
- Make informed decisions about when to use a framework vs. when to build custom

## License

MIT

## Author

**Faraz Ahmed** — Python & Web Dev Educator | Building toward Senior Agentic AI Engineer

- GitHub: [@farazahmediu01](https://github.com/farazahmediu01)
- LinkedIn: [Faraz Ahmed](https://www.linkedin.com/in/faraz-ahmed-01/)
