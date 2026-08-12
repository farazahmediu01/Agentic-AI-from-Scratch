# SDK Bridge

> **Our implementation → SDK abstraction → what the SDK is doing for us.**
>
> This table grows one chapter at a time. It is the single most valuable page in the repository: by the end, it is a complete map of the OpenAI Agents SDK expressed in code you personally wrote.
>
> It is also the **de-verbosified index of Agent Factory** — see `references/agent-factory-map.md`. When the course updates, you diff concept names against this table instead of re-reading prose.

## The whole SDK in three primitives

```python
Agent(...)        # what it is:  instructions + tools + model
Runner.run(...)   # the loop
@function_tool    # a capability
```

Sessions, handoffs, guardrails, tracing, streaming, approvals — **every one is a modifier of one of these three.** When a new feature appears, ask: is it changing the *agent*, the *run*, or a *tool*?

---

## Chapter 1 — The Agent Loop

**Axes:** 🧠 State · 🔒 Trust · 📐 Proof

| We built | SDK abstraction | What it does for us |
|---|---|---|
| `for iteration in range(1, MAX_ITERATIONS + 1)` | `Runner.run(agent, input)` | Runs the loop, detects the exit condition, returns a result object |
| `MAX_ITERATIONS = 15` | `max_turns=15` | Same circuit breaker — but **raises `MaxTurnsExceeded`** instead of returning a message |
| `messages: list[...]` + manual `.append()` | managed internally | Assistant/tool message threading and `tool_call_id` wiring |
| `TOOL_SCHEMAS` — ~140 lines of hand-written JSON Schema | `@function_tool` | Generates the schema from **type hints + docstring** |
| `"description": "..."` in the schema | the function's **docstring** | Same job, new location. Practice 5's lesson still applies |
| `"enum"`-by-prose in a description | `Literal["a", "b"]` | A closed set the SDK enforces *before* your function body runs |
| `TOOL_REGISTRY: dict[str, Callable]` | `tools=[...]` | Name→callable dispatch + argument validation |
| `json.loads(tool_call.function.arguments)` | handled | Parsing and type coercion |
| `try/except` around dispatch | handled | Tool exceptions returned to the model, same as ours |
| `system_prompt=` | `instructions=` | Identical concept |
| `assistant_message.content` | `result.final_output` | The final answer |
| our `AgentRun` + `summary()` | `result.new_items`, `result.raw_responses` | Typed item stream — messages, tool calls, tool outputs. **See the note below** |
| `client = OpenAI(base_url=...)` | `OpenAIChatCompletionsModel(openai_client=...)` | Same provider swap; the SDK is not tied to OpenAI |
| *(we hardcoded the client)* | `shared.models.make_model()` | Our own seam, not the SDK's: one `AGENT_PROVIDER` env var swaps Chat Completions/Gemini for Responses/OpenAI |
| *(we ran tools sequentially)* | parallel tool execution | Concurrency we did not build |
| *(nothing)* | `Runner.run_streamed()` | Token streaming |

### 🧠 The item stream is the Responses API, in disguise

The single most important row above is `result.new_items`, and it is worth stating plainly what it is.

Our loop read **one object**: `response.choices[0].message`, which carried `content` and/or `tool_calls` together. The SDK hands back **a list of separate typed items** instead:

```
MessageOutputItem   ToolCallItem   ToolCallOutputItem   ReasoningItem   HandoffCallItem …
```

That list shape is not the SDK's invention — **it is the OpenAI Responses API's output format.** The Responses API natively returns `response.output` as a list of items, and the Agents SDK adopted it as its universal internal currency.

So when we run on Chat Completions, the SDK **converts**: it takes the single `choices[0].message` we hand-parsed in Chapter 1 and fans it out into Responses-shaped items. One assistant reply with two `tool_calls` becomes one `MessageOutputItem` and two `ToolCallItem`s. The translation is a real file you can open:

```
agents/models/chatcmpl_converter.py
```

**Why this matters:** you are not learning a Chat-Completions-only mental model. Every `result.new_items` loop you write is Responses-shaped. The wire format underneath changed; your code did not. That is the whole argument for the seam in `shared/models.py`.

> Full comparison — state ownership, hosted tools, reasoning persistence, and what our path gives up: **[`RESPONSES_VS_CHATCOMPLETIONS.md`](RESPONSES_VS_CHATCOMPLETIONS.md)**.

### What does NOT transfer to the SDK

Worth stating plainly, because "just use the framework" should be a decision, not a reflex:

- **Visibility.** Our loop printed every step. The SDK hides them until you inspect `result.new_items`. First move when an SDK agent misbehaves: make it visible again.
- **Judgement.** The SDK removes plumbing, not decisions. The system-prompt rule that stops the agent silently "fixing" a negative amount is still yours to write — no framework will write it for you.
- **Turn semantics.** Our loop batches parallel tool calls into one iteration; the SDK often issues them one per turn. Identical work, different counts. **Never assert on turn count in an eval.**

---

## Chapter 2 — Typed Tools

**Axes:** 🔒 Trust · 📐 Proof

| We built | SDK abstraction | What it does for us |
|---|---|---|
| `@tool` — `inspect.signature` → `create_model` → `model_json_schema` | `@function_tool` | The same three moves. Ours is ~30 lines; theirs handles varargs, context params and docstring `Args:` sections |
| `Tool.args_model` (a Pydantic model per tool) | `schema.params_pydantic_model` | Genuinely the same object, built the same way |
| `Tool.schema` / `Tool.parameters` | `tool.params_json_schema` | The generated contract, for inspection and tests |
| `ConfigDict(extra="forbid")` | `additionalProperties: false` | Same decision reached independently: an invented argument must be an error, not a silent no-op |
| `Tool.call(raw)` — parse → validate → dispatch | `FunctionTool.on_invoke_tool(ctx, raw)` | Identical order. **Neither enters the function body on a bad argument** |
| `Literal[...]` in a signature | `Literal[...]` in a signature | Unchanged — this is Python, not the SDK. Chapter 1 could only ask for a closed set in prose |
| `Annotated[float, Field(gt=0)]` | same | Range and format constraints, published to the model and enforced at the door |
| `ToolError` — a failure the MODEL owns | `ModelBehaviorError` + `failure_error_function` | Same split between "the model can fix this" and "the model cannot" |
| `explain(name, exc)` | `default_tool_error_function` | **Ours is better.** See the note below |
| `_clean_schema()` (drops `title`, renames `gt`→`exclusiveMinimum`) | *(none needed — but see the note)* | A custom validator makes Pydantic emit raw constraint names that are not JSON Schema. Silent, and it costs a round trip |
| `MAX_INVALID_CALLS` | *(nothing)* | The SDK bounds turns, not wrongness. See below |
| `AgentRun.executed_names` | *(not recoverable)* | See below |
| *(nothing)* | `strict_json_schema=True` | Provider-side constrained decoding — a layer beneath us, in the model server |
| *(nothing)* | `is_enabled=`, `RunContextWrapper` first arg | Tools that appear conditionally, and per-run dependencies. Later chapters |

### 🔒 The SDK's error default is a privacy decision, not an oversight

Out of the box, a rejected tool call reaches the model as exactly `"Invalid JSON input for tool add."` — not which argument, not what type, not what was sent.

```python
# agents/_debug.py
DONT_LOG_TOOL_DATA = _debug_flag_enabled("OPENAI_AGENTS_DONT_LOG_TOOL_DATA", default=True)
```

Tool arguments carry personal data. Echoing them into errors, logs and traces **by default** would be a privacy incident waiting for its first enterprise customer. So the SDK chose privacy over recoverability — **and chose on your behalf.**

`failure_error_function=` hands the decision back, and does it **per tool**, which is where the tradeoff actually lives: verbose for `add`, silent for `charge_credit_card`. A global env var cannot express that.

> Generalise this past the one flag: **a framework's defaults encode somebody else's judgement about your tradeoffs.** Knowing the mechanism is what lets you notice when you disagree. That is the argument for building first, in one sentence.

### 🔒 Two things that do NOT transfer

**There is no rejection budget.** `max_turns` bounds how *long* the agent talks; our `MAX_INVALID_CALLS` bounds how *wrong* it is allowed to be. A model stuck re-sending the same invalid argument will spin to `max_turns`, paying per lap. If you want it to stop sooner you build that yourself — a counter in `RunHooks`, a context object, or a guardrail.

**"Attempted" and "executed" stop being distinguishable.** Our loop catches `ToolError`, so `AgentRun.executed_names` is exact. The SDK swallows the failure and returns your error string as the tool output, so a rejected call and a successful one look identical from outside: a `ToolCallItem`, then a `ToolCallOutputItem`. `solutions/expense_agent_sdk.py` recovers the fact by matching a prefix of a message it wrote itself — a hack, left in on purpose.

> **An abstraction that handles an event for you also decides how much of that event you may see afterwards.** Worth naming every time you meet it, rather than discovering it during an incident.

### 📐 What the chapter unlocked for testing

Moving validation to the boundary made the boundary a **pure function of a JSON string** — no model, no network, no key. That is why Chapter 2 has 46 unit tests running in 2 seconds, and Chapter 1 had none.

The standing rule from here on:

| Question | Where it belongs |
|---|---|
| Is `-450` rejected? Is `'astrology'` rejected? Does the enum reach the schema? | `pytest` — a property of the boundary, free, milliseconds |
| Did the agent ask instead of guessing? Did it recover from a rejection? | the golden dataset — needs a model, costs minutes |

---

## Chapters 3+ — to come

Rows are added as each chapter lands. Planned coverage, in the order the curriculum will build it:

| Concept | Likely SDK abstraction |
|---|---|
| Structured outputs | `output_type=` |
| Per-run dependencies | `RunContextWrapper`, `context=` |
| Conversation memory | `SQLiteSession` |
| Context window management | compaction / summarisation |
| Specialists & routing | `handoffs=[...]`, agents-as-tools |
| Guardrails | `@input_guardrail`, `@output_guardrail` |
| Human approval | `needs_approval=True` |
| Observability | `RunConfig`, tracing |
| Evals | our harness (the SDK does not provide this) |
| **Hosted tools** (paid chapter, last) | `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `HostedMCPTool` — **Responses API only**; flip `AGENT_PROVIDER=openai` |
