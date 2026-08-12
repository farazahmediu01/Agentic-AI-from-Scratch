# Responses vs Chat Completions

> **Why this curriculum runs on Chat Completions, what that costs you, and where the escape hatch is.**
>
> Read this once, early. It answers the question every student eventually asks: *"the Agents SDK docs use `Agent(model='gpt-4o')` — why does our code look different?"*

**Axes:** 🧠 State (who owns the transcript) · 🔒 Trust (which tools are allowed to exist)

---

## The one-sentence version

Chat Completions is a **stateless function**: you send the whole conversation, you get one message back. Responses is a **stateful service**: you send a pointer to the last turn, the server keeps the transcript, and it can run tools on its own hardware before replying.

The OpenAI Agents SDK defaults to Responses. We deliberately use Chat Completions.

---

## Mental model

Think of two ways to work with an accountant.

**Chat Completions** — you post the accountant the entire folder every single time. Every receipt, every prior letter. They read the folder, write one reply, and post the whole thing back. They remember nothing. **You own the filing cabinet.**

**Responses** — the accountant keeps your folder in their office. You send a note saying *"re: our last letter, ref #8842"*. They already have everything. They can also walk to the library themselves and look something up before replying. **They own the filing cabinet.**

Neither is smarter. They differ in *who holds the state* and *what the accountant can do without asking you*.

---

## The comparison

| | Chat Completions (ours) | Responses (SDK default) |
|---|---|---|
| **State ownership** 🧠 | **Client.** You resend the full message list every turn | **Server.** `previous_response_id` / `store=true` |
| **Request payload** | grows every turn — the whole transcript | a pointer plus the new input |
| **Output shape** | one object: `choices[0].message` | a **list** of typed items: `response.output` |
| **Item types** | `content` and/or `tool_calls` | `message`, `function_call`, `reasoning`, `web_search_call`, `file_search_call`, `mcp_call`, … |
| **Tool call id field** | `tool_calls[i].id` | `call_id` |
| **Returning a tool result** | `{"role": "tool", "tool_call_id": ...}` | a `function_call_output` item with `call_id` |
| **Hosted (server-run) tools** 🔒 | **none** | web search, file search, code interpreter, computer use, image gen, hosted MCP |
| **Reasoning across turns** | dropped between turns | preserved as `reasoning` items |
| **Works with Gemini / Claude / local** | **yes**, via OpenAI-compatible endpoints | OpenAI only |
| **Cost to learn on** | **free** (Gemini free tier) | paid |

---

## Why we chose the "old" one

Three reasons, in ascending order of importance.

**3. It's free.** Gemini exposes an OpenAI-compatible endpoint at `/v1beta/openai/`, which speaks Chat Completions. Nobody gets billed for learning.

**2. It's portable.** Real client work runs on whatever model the budget and compliance allow. An architect who only knows the OpenAI-hosted happy path is *less* employable, not more.

**1. Chapters 3 and 4 are impossible on server-side state.** This is the real reason.

Chapter 3 is the Context Window Manager. Chapter 4 is Memory. Both require that every byte the model sees lives in a list **inside your process**, where you can count it, prune it, summarise it, and budget it. If the server holds the transcript behind a `previous_response_id`, there is nothing in your process to manage. The lesson evaporates.

You cannot learn to manage a context window you are not holding.

### Practice 1 — feel the statelessness 🧠

Open `01_agent_loop/from_scratch/agent.py`. Find the `messages` list.

Add one line right before `client.chat.completions.create(...)`:

```python
print(f"  [sending {len(messages)} messages, {sum(len(str(m)) for m in messages)} chars]")
```

Run it.

**You're done when** you can state, from the printed numbers, what happens to the request size on each iteration and why — and can answer: *at 200 turns, what breaks?* That answer is Chapter 3's entire reason to exist.

---

## What we actually give up

Be honest about it — "just use the framework default" should be a decision, not a reflex.

**1. Hosted tools — the real gap.** These SDK classes exist and simply do not work on `OpenAIChatCompletionsModel`:

```
WebSearchTool   FileSearchTool   CodeInterpreterTool
ComputerTool    ImageGenerationTool   HostedMCPTool
```

They are executed on OpenAI's servers, not yours. There is no Chat Completions equivalent — the capability lives in the API, not the SDK. We hand-roll a web-search tool from scratch instead, then meet the hosted version in the late chapter (below).

**2. Reasoning persistence.** On Responses, a reasoning model's chain of thought carries across turns as `reasoning` items. On Chat Completions it is discarded. The SDK knows this hurts and ships a partial workaround — look at the `should_replay_reasoning_content` parameter on `OpenAIChatCompletionsModel`, and `agents/models/reasoning_content_replay.py`. That parameter existing *is* the evidence that the gap is real.

**3. Server-side sessions.** `OpenAIConversationsSession` wraps `previous_response_id`. We use `SQLiteSession` instead — client-side, works everywhere, and far better for teaching, since you can open the database and read what the agent remembers.

---

## The part that transfers for free

Here is the reassuring bit, and the thing most people get wrong.

**Roughly 85% of the Agents SDK never touches this choice.** `Agent`, `Runner`, `@function_tool`, `handoff()`, `@input_guardrail`, `output_type=`, `RunContextWrapper`, `RunHooks`, `SQLiteSession` — all provider-agnostic. Handoffs are literally function tools underneath.

And the deepest one: **the SDK converts Chat Completions responses into Responses-shaped items internally.** When you write

```python
tool_calls = [i for i in result.new_items if isinstance(i, ToolCallItem)]
```

that typed item stream *is* the Responses output model. The translation lives in `agents/models/chatcmpl_converter.py`. So you have been learning the Responses mental model this whole time — just approaching it from underneath.

### Practice 2 — see the conversion happen 🧠

`agent_sdk.py` already prints the tool calls it found in `result.new_items`. Add this beneath that loop:

```python
for i, item in enumerate(result.new_items):
    print(f"  [{i}] {type(item).__name__:22} raw={type(item.raw_item).__name__}")
```

Run it.

**You're done when** you can explain why a single Chat Completions reply containing `tool_calls` turned into *several* separate items — and name which file did the converting.

### Challenge — prove the shapes differ

Write a throwaway script that calls Gemini's endpoint **twice** with the OpenAI SDK directly (no Agents SDK): once via `client.chat.completions.create(...)`, and once via `client.responses.create(...)`.

**You're done when** you can state exactly what the second call does — and whether the failure (if it fails) comes from the SDK, the endpoint, or the model. Predict before you run. That distinction is the whole lesson: *the wire format is a property of the endpoint, not of the library.*

---

## The escape hatch

The switch is already built. `shared/models.py`:

```python
AGENT_PROVIDER=gemini   # Chat Completions, free      (default)
AGENT_PROVIDER=openai   # Responses, paid, hosted tools
```

Every `with_sdk/` file calls `make_model()` and nothing else. Check where you are pointed, without spending a token:

```powershell
uv run python -m shared.models
```

`from_scratch/` files deliberately **do not** use the factory. They keep building their client inline, because seeing the wire is the entire point of that layer.

---

## Verdict

| Chapters | Path | Why |
|---|---|---|
| 1–5 (loop, tools, context, memory, evals) | **Chat Completions / Gemini** | free, portable, and *required* for the state chapters to work |
| Hosted-tools chapter | **Responses / OpenAI** | the capability does not exist anywhere else |

One environment variable moves between them. That is what the seam bought us.
