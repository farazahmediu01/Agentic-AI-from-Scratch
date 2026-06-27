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
uv run python 01_agent_loop/agent.py
```

### Type Checking

```powershell
uv run pyright 01_agent_loop/agent.py
```

Target: **0 errors, 0 warnings** before moving to the next step.

---

## What's Off-Limits in This Workspace

- No `from agents import Agent` / no `from claude_agent_sdk import ...`
- No LangChain, no LlamaIndex, no Haystack
- The OpenAI SDK is allowed only as a **transport layer** to the model. Every loop, tool, memory, eval, and guardrail is hand-rolled.

If a framework solves it in 3 lines, we write the 30 lines underneath so we know what those 3 lines *cost*.

---

## Curriculum Design Principles

### Every Step Follows This Structure

```
step_folder/
  README.md       # Concept explanation + mental model + code walkthrough
  *.py            # Working implementation (the "build")
  EXERCISES.md    # Guided tasks for students (the "practice")
```

### The README teaches the "why" before the "how"

Each step's README starts with a mental model (analogy), then maps it to code, then walks through the implementation line by line. Students should read the README first, then read the code, then run it.

### The exercises are mandatory, not optional

Exercises are how students prove they understood the step — not by reading, but by building. Each exercise set includes:

1. **Warm-up** — a small modification to the existing code (e.g., add a new tool, change a behavior). Tests that the student can read and edit the code.
2. **Guided build** — a structured task that requires applying the step's concepts to build something new and useful. Includes clear acceptance criteria so students know when they're done.
3. **Challenge** — an open-ended problem that forces deeper thinking. No step-by-step instructions. Students must design the solution themselves using what they learned.

### Exercises connect to the bigger picture

Every exercise should feel like it's building toward a real agent — not a toy. The warm-up might add a tool. The guided build might create a mini-agent for a real task. The challenge might expose a limitation that the next step will solve.

### Acceptance criteria are explicit

Every exercise ends with "You're done when..." followed by concrete, checkable conditions. No fuzzy milestones. Students and instructors should both be able to verify completion.

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

Step 1 (`01_agent_loop/`) is complete with:
- `agent.py` — the five-step agent loop with `MAX_ITERATIONS` safety, error handling, and proper OpenAI SDK types
- `tools.py` — five tools (`get_current_time`, `add`, `multiply`, `subtract`, `divide`) with JSON schemas and a dispatch registry
- `README.md` — concept explanation with kitchen analogy, code walkthrough, self-check questions, common pitfalls
- Passes `pyright` with 0 errors

---

## Development Commands

| Task | Command |
|------|---------|
| Install / sync dependencies | `uv sync` |
| Run a step | `uv run python 01_agent_loop/agent.py` |
| Type check a file | `uv run pyright 01_agent_loop/agent.py` |
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
