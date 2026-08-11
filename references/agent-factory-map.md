# Agent Factory — Concept Map (snapshot)

**Source:** [Build AI Agents with the OpenAI Agents SDK: A 90-Minute Crash Course](https://agentfactory.panaversity.org/docs/build-agents-crash-course)
**Snapshot taken:** 2026-08-12
**Why this file exists:** Agent Factory changes often and reads long. This page is the *durable* layer — 16 concept names and their SDK abstractions. Re-check quarterly by diffing **concept titles only**. Never re-read the prose unless a title changed.

## The rule for using this source

| Layer | Examples | Re-read when |
|---|---|---|
| **Durable** | concept names, SDK abstractions, the state/trust framing | a title changes in the diff |
| **Volatile** | model names, prices, Cloudflare/R2 infra, screenshots | you actually need that specific thing, and never for learning |

Agent Factory's organizing claim: **"every agent bug is either a state bug or a trust bug."** We adopt it, extended with a third axis — **Proof** — because knowing an agent works is its own discipline and the SDK does not provide it.

## The 16 concepts

| # | Concept | SDK surface | Our chapter | Status |
|---|---|---|---|---|
| 1 | What an agent actually is | loop vs single completion | Ch1 | ✅ covered, deeper |
| 2 | The SDK in three primitives | `Agent`, `Runner`, `@function_tool` | Ch1 Layer 4 | ✅ covered |
| 3 | The agent loop, made concrete | `max_turns` | Ch1 | ✅ covered, deeper |
| 4 | Project setup with `uv` | `pyproject.toml`, `uv.lock` | Ch1 setup | ✅ covered |
| 5 | The chat loop, and its bug | statelessness demonstrated | memory chapter | ⏳ planned |
| 6 | Sessions, fixing the bug | `SQLiteSession` | memory chapter | ⏳ planned |
| 7 | Streaming responses | `Runner.run_streamed`, `stream_events()` | TBD | ⏳ planned |
| 8 | Function tools, beyond the stub | type hints, `Literal`, Pydantic returns | Ch2 | ⏳ next |
| 9 | Handoffs to specialist agents | `handoffs=[...]` | specialists chapter | ⏳ planned |
| 10 | Guardrails | `@input_guardrail`, `@output_guardrail`, `@tool_input_guardrail` | guardrails chapter | ⏳ planned |
| 11 | Tracing | `RunConfig`, `trace_metadata` | observability chapter | ⏳ planned |
| 12 | Switching models / cost routing | `OpenAIChatCompletionsModel`, `LitellmModel` | principle only — **never hardcode prices** | ⏳ partial |
| 13 | Human approval for risky tools | `needs_approval=True`, `state.approve()` | trust chapter (seeded as Ch1 Exercise 7) | ⏳ planned |
| 14 | Sandboxes / `SandboxAgent` | `Capabilities`, `Manifest` | — | ❌ deferred |
| 15 | Cloudflare bridge + R2 mounts | worker routing, `RemoteBucket` | — | ❌ not adopted |
| 16 | Compaction | `Compaction()` | context chapter (ours is deeper) | ⏳ planned |

**Concepts 14–15 are deliberately out of scope.** Vendor infrastructure, fastest-rotating content in the course, orthogonal to agent fundamentals. Revisit only if a deployment module is added.

## What we took from their pedagogy

| Technique | Where we use it |
|---|---|
| **PRIMM** — Predict → Run → Investigate → Modify → Make | inline practices; prediction + confidence 1–5 + `<details>` spoiler |
| **Bug-first sequencing** — show the failure, then the fix | Practice 4 (infinite loop), Practice 5 (vague description), project case 5 |
| **Cluster checkpoints** — "✓ the frame is in place" | two per chapter, marking safe stopping points |
| **Cost visibility** — "how many model calls does this cost?" | budget line in each chapter header |
| **One project across the whole course** | Spendly Lite, grown chapter by chapter |
| **"Three primitives, everything else is a modifier"** | top of `SDK_BRIDGE.md` |

## What we deliberately did not take

- **16 concepts in 90 minutes.** The density is the problem we're solving.
- **Named models and price tables.** They rot. We teach the routing principle instead.
- **Coding-agent-does-the-typing** (`AGENTS.md` brief). Students type the loop themselves in the early chapters.
- **State/Trust as the top-level sequence.** Adopted as tags, rejected as ordering — the project needs the two interleaved.

## Related local source

`C:\Users\Faraz\Desktop\tech-guide\notes\chapter-34-openai-agents-sdk\` — deeper than the crash course on Agents/Runner (L1), function tools & `RunContextWrapper` (L2), and agents-as-tools (L3). Use Chapter 34 for depth, this map for the checklist.
