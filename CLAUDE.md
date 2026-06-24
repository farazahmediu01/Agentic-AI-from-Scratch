# Agentic AI From Scratch

A learning workspace where every core primitive of an agentic AI system is built **without frameworks**, using only the raw model API and a Python `while` loop.

The goal is not to ship a framework. The goal is to understand — at the level of "I could re-implement this from memory" — how production agentic systems actually work under the hood. After this, frameworks like OpenAI Agents SDK and Claude Agent SDK stop feeling like magic and start feeling like reasonable engineering choices on top of patterns you've already built.

---

## The Roadmap (Stage 1 — Build the Primitives)

| Step | Primitive | Folder |
|------|-----------|--------|
| 1 | **The Agent Loop** — call model → parse → execute tool → feed back → repeat | `01_agent_loop/` |
| 2 | **Manual Tool Use** — hand-rolled JSON schema generation, parsing, dispatch (no `tools=` shortcut) | `02_manual_tool_use/` |
| 3 | **Context Window Manager** — message-list pruning, summarization, token budgeting | `03_context_manager/` |
| 4 | **Memory** — message persistence, summary memory, semantic recall via embeddings | `04_memory/` |
| 5 | **Eval Harness** — golden dataset + LLM-as-judge from scratch | `05_evals/` |
| 6 | **Guardrails** — input classifier + output validator + tripwire | `06_guardrails/` |

Once these six are built, we'll read the source of `openai-agents-python` and `claude-agent-sdk` to see how the production frameworks implement the same ideas — and what they add that we didn't.

---

## Stack

| Choice | Why |
|--------|-----|
| **Python 3.12+** | Type hints, modern stdlib |
| **`openai` SDK** | Used against any OpenAI-compatible endpoint — including Gemini's `/v1beta/openai/` |
| **`python-dotenv`** | Keep API keys out of source |
| **No agent framework** | The whole point |

You'll use **Gemini free models via the OpenAI-compatible endpoint** so cost is zero while learning.

---

## Setup (one time)

```powershell
cd C:\Users\Faraz\Desktop\agentic-ai-from-scratch
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Now open .env and paste your Gemini API key
```

Get a free Gemini API key here: https://aistudio.google.com/apikey

---

## Run Step 1

```powershell
cd 01_agent_loop
python agent.py
```

You should see the agent visibly *loop* — calling tools, getting results, calling more tools, then producing a final answer.

---

## What's Off-Limits in This Workspace

- No `from agents import Agent` / no `from claude_agent_sdk import ...`
- No LangChain, no LlamaIndex, no Haystack
- The OpenAI SDK is allowed only as a **transport layer** to the model. Every loop, tool, memory, eval, and guardrail is hand-rolled.

If a framework solves it in 3 lines, we want to write the 30 lines underneath so we know what those 3 lines *cost*.
