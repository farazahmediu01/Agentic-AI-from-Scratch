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
| our `AgentRun` + `summary()` | `result.new_items`, `result.raw_responses` | Typed item stream — messages, tool calls, tool outputs |
| `client = OpenAI(base_url=...)` | `OpenAIChatCompletionsModel(openai_client=...)` | Same provider swap; the SDK is not tied to OpenAI |
| *(we ran tools sequentially)* | parallel tool execution | Concurrency we did not build |
| *(nothing)* | `Runner.run_streamed()` | Token streaming |

### What does NOT transfer to the SDK

Worth stating plainly, because "just use the framework" should be a decision, not a reflex:

- **Visibility.** Our loop printed every step. The SDK hides them until you inspect `result.new_items`. First move when an SDK agent misbehaves: make it visible again.
- **Judgement.** The SDK removes plumbing, not decisions. The system-prompt rule that stops the agent silently "fixing" a negative amount is still yours to write — no framework will write it for you.
- **Turn semantics.** Our loop batches parallel tool calls into one iteration; the SDK often issues them one per turn. Identical work, different counts. **Never assert on turn count in an eval.**

---

## Chapters 2+ — to come

Rows are added as each chapter lands. Planned coverage, in the order the curriculum will build it:

| Concept | Likely SDK abstraction |
|---|---|
| Typed tools & validation | `@function_tool`, `Literal`, Pydantic args |
| Structured outputs | `output_type=` |
| Per-run dependencies | `RunContextWrapper`, `context=` |
| Conversation memory | `SQLiteSession` |
| Context window management | compaction / summarisation |
| Specialists & routing | `handoffs=[...]`, agents-as-tools |
| Guardrails | `@input_guardrail`, `@output_guardrail` |
| Human approval | `needs_approval=True` |
| Observability | `RunConfig`, tracing |
| Evals | our harness (the SDK does not provide this) |
