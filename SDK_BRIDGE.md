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

## Chapter 3 — Structured Outputs

**Axes:** 📐 Proof · 🧠 State

| We built | SDK abstraction | What it does for us |
|---|---|---|
| `JSON_PROMPT` — 11 lines describing keys, begging for no code fences | *(nothing)* | The schema **is** the description. Nothing to write, nothing to drift out of sync |
| `json.loads(raw)` | handled | Parsing — 3/8 of real responses survived it |
| `_FENCE` / `_FIRST_OBJECT` / `_TRAILING_COMMA` regexes | *(unnecessary)* | Constrained generation means there are no fences to strip |
| `ExpenseReply.model_validate(parsed)` | handled | Validation, before `final_output` exists |
| a retry-and-repair loop | handled | Retry on a malformed response |
| *(we could not build this)* | `"strict": true` in `response_format` | **Constrained decoding in the model server** — a layer beneath us |
| `dict[str, Any]` at the call site | `result.final_output: YourModel` | A typed object; `pyright` checks the fields you read |
| four optional branch fields | `output_type=SpendlyReply` | One argument replaces the whole ladder |
| `@model_validator` — exactly one branch | *(nothing)* | See below |
| `Category` (Ch2's `Literal`) on an output field | same | The closed set now constrains what the agent **says**, not just what it calls |

### 📐 The eval upgrade is the real payoff

Chapter 2 made the *input* boundary a pure function and bought 46 offline unit tests. Chapter 3 makes the *output* a typed value and buys evals that mean something:

```python
# Chapter 2 — a classifier built out of str.find
("the answer states 17500", "17500" in answer)
("it asks for the amount",  "how much" in answer or "amount" in answer)

# Chapter 3
("remaining is correct",    run.reply.logged.remaining == 17500)
("it asked for the RIGHT thing", run.reply.need_more_info.missing == ["category"])
```

The first pair is wrong in both directions — `"17500" in answer` passes on *"you spent 17500 of your 17500 budget"*, and `"amount" in answer` passes on *"I logged that amount."* **Structured outputs are not a feature; they are what makes evaluation possible**, which is why they land before the evals chapter rather than after.

### 🔒 Three things that do NOT transfer

**A shape is not a fact.** `output_type=` guarantees `remaining` is a float. It guarantees nothing about whether that float matches what `subtract` returned. Chapter 2 §7b showed that a type stops a bad value but not an invented one; the Chapter 3 version is that a schema stops a malformed answer but not a well-formed false one. Same failure, better clothes.

**"Exactly one of these" is not expressible.** A union of four optional fields satisfies its schema when zero are set and when two are. JSON Schema cannot portably say otherwise, so `replies.py` enforces it in a `@model_validator` that runs *after* the model has spoken. That is a guardrail — the first one in the curriculum — and Chapter 8 gives it a decorator.

**Your retry budget is still yours.** The SDK retries a malformed response. It does not retry the free-tier 429 that actually stops your demo, and Chapter 1's hand-rolled backoff was silently lost in the move to `Runner.run`. Generalise it: **when you adopt a framework, the things you built that it does not provide do not announce themselves on the way out.**

---

## Chapter 4 — Sessions & State

**Axes:** 🧠 State

The first chapter with nothing hand-rolled. Both mechanisms are SDK-native by policy — a
session is a table, and a context object is a Python argument. The left column below is
therefore Chapter **1**'s code, because that is the last time we built any of this.

| We built (Ch1) | SDK abstraction | What it does for us |
|---|---|---|
| `messages: list[dict] = []` | `SQLiteSession(session_id, db_path)` | Storage, durable instead of a local variable |
| `messages.append({"role": "user", ...})` | `session=` on `Runner.run` | Appends the user turn before the run and the assistant turn after |
| appending tool results by hand | handled | Tool calls and results stored as correctly paired separate items |
| passing `messages` into the next call | handled | Loaded and prepended automatically |
| *(nothing)* | `session.get_items()` / `add_items()` / `pop_item()` / `clear_session()` | Read, seed, repair and reset a transcript |
| a module-level `MONTHLY_BUDGETS` dict | `RunContextWrapper[User]` | Per-run dependencies — works for a second user |
| interpolating user data into the prompt | `context=` on `Runner.run` | Not tokens, not visible to the model, not roundable |
| threading `user` through every call | first parameter, injected | And **stripped from the tool schema** the model reads |
| `Agent(...)` | `Agent[User](...)` | Nothing at runtime; everything at edit time |

### 🧠 The stored shape is Chapter 1's list, exactly

```
[ 0] user                    Pack two t-shirts, they're 0.2 kg each.
[ 1] function_call:add_item  {"item":"t-shirt","kg":0.2}
[ 2] function_call_output    Packed t-shirt (0.2 kg). Bag now 0.2 kg.
[ 3] assistant               I've packed both t-shirts for you.
```

Same roles, same call/result pairing, same append-only growth. `with_sdk/session_demo.py`
prints it next to the raw JSON so there is nowhere for magic to hide.

### 🔒 The context is invisible until a tool reveals it

```
whoami   model is told about: (no arguments)
add_item model is told about: ['item', 'kg']
```

Every one of those declares `ctx: RunContextWrapper[Traveller]` first, and none of them
mentions it. **A prompt injection cannot reach `ctx.context` — there is no argument to
poison.**

The half people skip: a tool *return value* is stored in the session like everything else.
Measured, in `context_demo.py`:

```
session where a tool returned the name   -> 'Faraz' in transcript: True
session where no tool returned it        -> 'Faraz' in transcript: False
```

> **A context is private until a tool returns part of it.** After that it is in the
> transcript permanently and re-sent every turn. "What does this tool return?" is a
> security question.

### 📐 What the chapter unlocked for testing

A session is storage and a context is a dataclass, so neither needs a model to be wrong —
13 offline tests, no API key, ~1 second. And Chapter 3's `RunLike` Protocol finally paid
off: `check_regression.py` runs **Chapter 3's nine cases against Chapter 4's agent** in
forty lines, because v4's `SdkRun` still satisfies a contract neither file mentions.

> **Depend on the shape you need, not the class you happen to have.**

### 🔒 Three things that do NOT transfer

**It does not scope the session for you.** `session_id` is an unvalidated string and
`db_path` defaults to `":memory:"`. Same id, different paths → two silent conversations.
Same id, same path → one silent conversation. `session_id` is an authorisation decision
wearing the costume of a cache key.

**It does not prune.** `SessionSettings(limit=N)` and `get_items(limit=N)` cap what you
**read**, never what you **store**, count items rather than tokens, and can slice a
`function_call` away from its `function_call_output`. Measured: at `limit=2` and `limit=6`
the window starts orphaned. That is Chapter 5.

**It does not keep the model honest about what it remembers.** A session makes stale
recital *possible*; nothing in the SDK makes it *unlikely*. Chapter 1's rule — *use tools
for every fact* — was easy when there was no memory to recall from. Generalise it: **every
primitive that removes a failure mode installs a new one, and the new one is always
quieter.**

---

## Chapters 5+ — to come

Rows are added as each chapter lands. Planned coverage, in the order the curriculum will build it — this table mirrors the roadmap in `CLAUDE.md`, and **anything past the next chapter is a hypothesis, not a promise**:

| Ch | Concept | Likely SDK abstraction |
|---|---|---|
| 5 | Context window management — Chapter 4's failure mode, measured in Ch4 §9 | compaction / summarisation |
| 6 | Evals | our harness (the SDK does not provide this) |
| 7 | Specialists & routing | `handoffs=[...]`, agents-as-tools |
| 8 | Guardrails & human approval | `@input_guardrail`, `@output_guardrail`, `needs_approval=True` |
| 9 | Observability — tracing, streaming, cost & token accounting | `RunConfig`, tracing, `Runner.run_streamed()` |
| 10 | Serving & MCP | FastAPI, `MCPServerStdio` / `MCPServerSse` |
| 11 | **Hosted tools** (the paid chapter) | `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `HostedMCPTool` — **Responses API only**; flip `AGENT_PROVIDER=openai` |
| 12 | Cold build capstone | all of the above, unfamiliar domain, no scaffolding |

**Evals land in the middle, not at the end.** From Chapter 6 onward, *"the eval suite is still green"* is an acceptance criterion for every later chapter — which is what converts a growing project into a compounding one, and is the closest thing in this curriculum to the daily experience of maintaining an agent.
