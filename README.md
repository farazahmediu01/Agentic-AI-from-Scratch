# Agentic AI From Scratch

Build every core primitive of an agentic AI system **without frameworks** — using only the raw model API and a Python `while` loop.

> If a framework solves it in 3 lines, we write the 30 lines underneath so we know what those 3 lines *cost*.

## Why This Exists

Most agentic AI tutorials start with `pip install agents` and call it a day. Students learn to *use* a framework but can't explain what happens inside it. When something breaks — and it always breaks — they're stuck.

This curriculum takes the opposite approach. We build every primitive by hand first: the agent loop, tool dispatch, context management, memory, evals, and guardrails. After that, frameworks like **OpenAI Agents SDK** and **Claude Agent SDK** stop feeling like magic and start feeling like reasonable engineering choices on top of patterns you've already built.

## Who This Is For

- **Instructors** looking for a structured, hands-on curriculum for teaching agentic AI fundamentals
- **Students** who want to understand how agents actually work, not just how to call an API
- **Self-learners** building toward production AI agent roles

**Prerequisites:** Basic Python (functions, dicts, loops, exceptions). No AI/ML background required.

## The Roadmap

Each step builds one primitive. Each step includes a concept explanation, working code, and exercises.

| Step | What You Build | Folder |
|------|---------------|--------|
| 1 | **The Agent Loop** — the `while` loop that powers every agent framework | `01_agent_loop/` |
| 2 | **Manual Tool Use** — hand-rolled JSON schemas, parsing, and dispatch | `02_manual_tool_use/` |
| 3 | **Context Window Manager** — message pruning, summarization, token budgeting | `03_context_manager/` |
| 4 | **Memory** — persistence, summary memory, semantic recall with embeddings | `04_memory/` |
| 5 | **Eval Harness** — golden dataset + LLM-as-judge, built from scratch | `05_evals/` |
| 6 | **Guardrails** — input classifier, output validator, tripwire | `06_guardrails/` |

## Stack

| Tool | Role |
|------|------|
| Python 3.12+ | Language |
| [uv](https://docs.astral.sh/uv/) | Package manager (replaces pip + venv) |
| OpenAI Python SDK | Transport layer to the model — nothing more |
| Gemini (free tier) | LLM provider via OpenAI-compatible endpoint — zero cost |
| pyright | Static type checker |

**No agent frameworks.** No LangChain, no LlamaIndex, no Haystack. The OpenAI SDK is used only to send messages and receive responses. Every loop, tool, memory system, eval, and guardrail is hand-rolled.

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
uv run python 01_agent_loop/agent.py
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
uv run pyright 01_agent_loop/agent.py
```

Target: 0 errors before moving to the next step.

## How Each Step Is Structured

Every step folder contains:

| File | Purpose |
|------|---------|
| `README.md` | Concept explanation with a mental model, code walkthrough, self-check questions, and common pitfalls |
| `*.py` | Working implementation — the "build" |
| `EXERCISES.md` | Guided tasks for students — warm-up, guided build, and challenge |

### Exercise philosophy

Each step includes three tiers of exercises:

1. **Warm-up** — modify the existing code (e.g., add a new tool). Proves the student can read and edit the implementation.
2. **Guided build** — apply the step's concepts to build something new and useful. Includes clear acceptance criteria.
3. **Challenge** — an open-ended problem with no step-by-step instructions. Forces the student to design the solution themselves.

Exercises build toward a real agent, not a toy. The warm-up adds a tool. The guided build creates a mini-agent for a real task. The challenge exposes a limitation that the next step solves.

## For Instructors

Each step is designed for a **90–120 minute session**:

| Phase | Duration | Activity |
|-------|----------|----------|
| Concept | 15–20 min | Walk through the README mental model. Ask questions before showing code. |
| Code walkthrough | 20–25 min | Read the implementation together. Run it. Trace the output. |
| Exercises | 45–60 min | Students work through warm-up and guided build. |
| Debrief | 10–15 min | Review solutions. Discuss what broke. Preview the next step. |

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
