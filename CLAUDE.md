# Agentic AI From Scratch

A hands-on curriculum where every core primitive of an agentic AI system is built **without frameworks**, using only the raw model API and a Python `while` loop.

This is not a personal experiment — it is a **teaching resource**. Instructors and students use this repository to learn, teach, and practice agentic AI from first principles. Every session must produce working code AND exercises that challenge students to build something real.

---

## Who This Is For

| Audience | How they use this repo |
|----------|----------------------|
| **Instructors** | Walk through each step in class, use the exercises as guided lab work, extend with their own challenges |
| **Students** | Follow the build, answer the self-check questions, complete the exercises to prove understanding |
| **Self-learners** | Work through steps sequentially, treat exercises as mandatory checkpoints before moving on |

**Prerequisite knowledge:** Basic Python (functions, dicts, loops, exceptions). No AI/ML background needed — that's what we're building here.

---

## The Goal

After completing all 6 steps, a student should be able to:

1. Explain how every production agent framework works under the hood
2. Build a working agent from scratch with tool use, memory, and guardrails
3. Read the source of OpenAI Agents SDK or Claude Agent SDK and understand every design choice
4. Evaluate whether an agent's output is correct using a hand-built eval harness

Frameworks like OpenAI Agents SDK and Claude Agent SDK stop feeling like magic and start feeling like reasonable engineering choices on top of patterns you've already built.

---

## The Roadmap (Stage 1 — Build the Primitives)

| Step | Primitive | Folder | Status |
|------|-----------|--------|--------|
| 1 | **The Agent Loop** — call model, parse, execute tool, feed back, repeat | `01_agent_loop/` | Done |
| 2 | **Manual Tool Use** — hand-rolled JSON schema generation, parsing, dispatch (no `tools=` shortcut) | `02_manual_tool_use/` | Pending |
| 3 | **Context Window Manager** — message-list pruning, summarization, token budgeting | `03_context_manager/` | Pending |
| 4 | **Memory** — message persistence, summary memory, semantic recall via embeddings | `04_memory/` | Pending |
| 5 | **Eval Harness** — golden dataset + LLM-as-judge from scratch | `05_evals/` | Pending |
| 6 | **Guardrails** — input classifier + output validator + tripwire | `06_guardrails/` | Pending |

Once these six are built, we read the source of `openai-agents-python` and `claude-agent-sdk` to see how the production frameworks implement the same ideas — and what they add that we didn't.

---

## Stack

| Choice | Why |
|--------|-----|
| **Python 3.12+** | Type hints, modern stdlib |
| **`uv`** | Fast, modern Python package manager — replaces pip + venv |
| **`openai` SDK** | Used against any OpenAI-compatible endpoint — including Gemini's `/v1beta/openai/` |
| **`python-dotenv`** | Keep API keys out of source |
| **`pyright`** | Static type checker — catches bugs before runtime |
| **No agent framework** | The whole point |

We use **Gemini free models via the OpenAI-compatible endpoint** so cost is zero while learning.

---

## Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed (`pip install uv` or see docs for platform-specific install)
- A free Gemini API key from https://aistudio.google.com/apikey

### Installation

```powershell
cd C:\Users\Faraz\Desktop\agentic-ai-from-scratch
uv sync
copy .env.example .env
# Open .env and paste your Gemini API key
```

`uv sync` reads `pyproject.toml`, creates the `.venv`, and installs all dependencies in one step.

### Run Step 1

```powershell
uv run python 01_agent_loop/from_scratch/agent.py
```

### Type Checking

```powershell
uv run pyright 01_agent_loop/
```

Target: **0 errors, 0 warnings** before moving to the next step.

---

## The Framework Rule (scoped, not absolute)

**Mastering the OpenAI Agents SDK is the goal. Building from scratch is how we make the SDK legible — it is the means, not the destination.**

Every chapter therefore contains both, in separate folders, under opposite rules:

| Folder | Rule |
|---|---|
| `from_scratch/` | **No agent framework.** No `from agents import ...`, no LangChain/LlamaIndex/Haystack. The OpenAI SDK is a transport layer only. Every loop, tool, memory, eval and guardrail is hand-rolled. |
| `with_sdk/` | **No hand-rolling.** Use the OpenAI Agents SDK as intended. Re-implementing what the SDK provides defeats the purpose of this layer. |

If a framework solves it in 3 lines, we write the 30 lines underneath so we know what those 3 lines *cost* — **and then we use the 3 lines.**

A student finishing a chapter must be able to say: *"I built this mechanism, I know what the SDK does instead, and I can name what it does for me."*

## The Three Axes (tag every chapter)

Agent Factory's framing — *"every agent bug is either a state bug or a trust bug"* — extended with the axis that matters most for this curriculum's weakest area:

| Axis | Question | Examples |
|---|---|---|
| 🧠 **State** | What does it remember? | the message list, context window, sessions, compaction |
| 🔒 **Trust** | What is it allowed to do? | tools as permissions, `max_turns`, guardrails, approval gates |
| 📐 **Proof** | How do we know it worked? | golden datasets, run evidence, traces, evals |

Tag each chapter and each concept. Make *"is this a state bug, a trust bug, or a proof gap?"* the standing debrief question.

---

## Curriculum Design Principles

### THE NON-NEGOTIABLE RULE — Practice Follows Every Concept

> **Reading is not learning. A student who only reads or watches forgets the concept before the next chapter and arrives at it unable to build.**

Therefore, in this repository, **no concept is ever taught without a hands-on task attached to it.** This is not a nice-to-have and it is not deferred to the end of the chapter. It applies to every section of every chapter, forever.

**The mandatory teaching pattern — apply it to every section:**

```
CONCEPT  ->  PRACTICE  ->  (CHALLENGE)  ->  ... repeat per section ...  ->  CHAPTER PROJECT
```

| # | Element | Rule |
|---|---------|------|
| 1 | **Teach the concept** | Beginner-friendly. Mental model / analogy first, then the code. Assume no AI background. |
| 2 | **Practice immediately** | A small hands-on task **inside the README, directly under the concept it teaches**. Never batched at the end of the file. Scoped to that one concept. Completable independently in 5–15 minutes. |
| 3 | **Challenge where it fits** | A short "push further" task that reinforces or stress-tests the concept. Optional per section, but the chapter must contain several. |
| 4 | **Chapter project** | Every chapter ends with a small practical project that **combines every concept in the chapter** into one working thing. Mandatory. No chapter is complete without it. |

**Difficulty must climb.** Practice tasks progress within a chapter (read → edit → extend → design) and across chapters. Practice 1 of a chapter should be near-trivial so every student gets an early win; the last one should require real thought.

**Never write a chapter as pure prose.** If a section explains something and does not ask the student to do something, the section is unfinished. When in doubt, add the task.

### The Six Layers — every chapter has all of them

| Layer | Where | What |
|---|---|---|
| 1 **Concept** | `README.md` | The mechanism, taught plainly, mental model first |
| 2 **From scratch** | `from_scratch/` | The student builds the mechanism by hand |
| 3 **Practice** | inline + `EXERCISES.md` | Predict, run, break, extend — with acceptance criteria |
| 4 **SDK** | `with_sdk/` | The same capability with the OpenAI Agents SDK |
| 5 **Bridge** | `../SDK_BRIDGE.md` | Our code → SDK abstraction → what it does for us |
| 6 **Project** | `PROJECT.md` | Spendly Lite gains one capability |

**Layer 4 is not optional.** A chapter that stops at the from-scratch implementation has failed its purpose. Students must always reach *"we built this manually — now let's see how the SDK provides it."*

```
step_folder/
  README.md       # Concept -> inline Practice -> Concept -> inline Practice -> ...
  from_scratch/   # hand-rolled implementation (no frameworks)
  with_sdk/       # same capability on the Agents SDK + compare.md
  EXERCISES.md    # The graded set: warm-up -> guided build -> challenge
  PROJECT.md      # Spendly Lite increment + acceptance checklist + rubric + Spendly Transfer
  solutions/      # Reference solutions (instructor grading + student self-check AFTER attempting)
```

### The project is ONE project

**Spendly Lite** — a personal expense assistant — is built in Chapter 1 and extended in every chapter after. Students never start a new unrelated project. Complexity grows; the codebase is continuous.

It deliberately mirrors the architecture of Spendly, Faraz's real WhatsApp expense product (intent → specialists → structured outputs → SQLite), but it is a clean-room teaching build: **no external services, no API keys beyond the model, no business-sensitive material.** Students must be able to run it with a free Gemini key and nothing else.

### 🔁 Spendly Transfer

Every chapter ends with a short, concrete task porting the chapter's concept into the **real** Spendly codebase (`C:\Users\Faraz\Desktop\Spendly\`). This satisfies the standing rule that Spendly is the spine, without coupling the curriculum to the product.

### The README teaches the "why" before the "how"

Each step's README starts with a mental model (analogy), then maps it to code, then walks through the implementation line by line — **with a `### Practice N` block after each concept**. Students read a concept, do the task, and only then move to the next concept.

### The exercises are mandatory, not optional

`EXERCISES.md` is the graded set students work through in the lab portion of the session. Three tiers:

1. **Warm-up** — a small modification to the existing code (e.g., add a new tool, change a behavior). Tests that the student can read and edit the code.
2. **Guided build** — a structured task that requires applying the step's concepts to build something new and useful. Includes clear acceptance criteria so students know when they're done.
3. **Challenge** — an open-ended problem that forces deeper thinking. No step-by-step instructions. Students must design the solution themselves using what they learned.

### Exercises connect to the bigger picture

Every exercise should feel like it's building toward a real agent — not a toy. The warm-up might add a tool. The guided build might create a mini-agent for a real task. The challenge might expose a limitation that the next step will solve.

### Acceptance criteria are explicit

Every practice task, exercise, and project ends with **"You're done when..."** followed by concrete, checkable conditions. No fuzzy milestones. Students and instructors should both be able to verify completion.

### Every chapter project must produce evidence

The chapter project requires a `RUNS.md` (or equivalent) capturing real runs and their outcomes. This starts the eval habit at Chapter 1 instead of Chapter 5 — by the time students reach the eval harness, recording agent behaviour is already muscle memory.

---

## Session Delivery Guide (for Instructors)

### Recommended session flow (90–120 minutes)

| Phase | Duration | Activity |
|-------|----------|----------|
| **Concept** | 15–20 min | Walk through the README mental model. Ask questions before showing code. |
| **Code walkthrough** | 20–25 min | Read the implementation together. Run it. Trace the output. |
| **Exercises** | 45–60 min | Students work through warm-up and guided build. Instructor circulates. |
| **Debrief** | 10–15 min | Review solutions. Discuss what broke and why. Preview what's missing (next step). |

### Key teaching moves

- **Don't show the code first.** Start with the mental model. Ask students to predict what the code should do before showing it.
- **Run before reading.** Let students see the output, then trace backward to understand how it was produced.
- **Let exercises fail.** The guided build and challenge are designed so students will hit real bugs. That's the learning. Don't preempt the failure.
- **Connect forward.** At the end of every session, name the limitation that the current step can't solve. That's the hook for the next session.

---

## Step 1 Completion State

Chapter 1 (`01_agent_loop/`) is complete with all six layers:
- `from_scratch/agent.py` + `tools.py` — the five-step loop with `MAX_ITERATIONS`, error handling, typed
- `with_sdk/agent_sdk.py` + `compare.md` — the same agent on `Agent`/`Runner`/`@function_tool`, plus the line-by-line map and Practices 10–11
- `README.md` — kitchen analogy, 9 concepts each with an inline practice, prediction + confidence + `<details>` spoilers, 2 checkpoints, State/Trust/Proof tags
- `EXERCISES.md` — 3 warm-ups, 2 guided builds, 2 challenges, all with acceptance criteria
- `PROJECT.md` — **Spendly Lite v1**, built twice (scratch + SDK) and graded by one golden dataset; includes the Spendly Transfer
- `solutions/` — `loop.py` (reusable, retries 429s), unit-converter agent, `expense_*` project builds, `check_expenses.py` (runs against either implementation)
- `../SDK_BRIDGE.md` — Chapter 1 rows filled in
- Passes `pyright` with 0 errors; both builds verified against the 5-case dataset

---

## Development Commands

| Task | Command |
|------|---------|
| Install / sync dependencies | `uv sync` |
| Run a step | `uv run python 01_agent_loop/from_scratch/agent.py` |
| Type check a chapter | `uv run pyright 01_agent_loop/` |
| Run the SDK build | `uv run python 01_agent_loop/with_sdk/agent_sdk.py` |
| Grade the project (both builds) | `uv run python 01_agent_loop/solutions/check_expenses.py [--impl sdk]` |
| Add a dependency | `uv add <package>` |

---

## Project Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | Project metadata and dependencies (uv reads this) |
| `uv.lock` | Locked dependency versions (commit this) |
| `.env.example` | Template for API keys — copy to `.env` and fill in |
| `.gitignore` | Excludes `.env`, `.venv`, `__pycache__` |
| `CLAUDE.md` | This file — project instructions for Claude Code |
