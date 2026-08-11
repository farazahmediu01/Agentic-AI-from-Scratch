# Layer 4 — The Same Agent, Two Ways

You just built the agent loop by hand. Now read `agent_sdk.py`. It does exactly what your loop does, with the same five tools and the same task.

Run them back to back:

```powershell
uv run python 01_agent_loop/from_scratch/agent.py
uv run python 01_agent_loop/with_sdk/agent_sdk.py
```

Same tool calls. Same final answer. **~250 lines → ~50 lines.**

---

## 🔨 Practice 10 — Predict the mapping (10 min)

Before reading the table below, open both files side by side and write down your answer to each:

1. Which SDK call replaced your `for iteration in range(MAX_ITERATIONS)` loop?
2. Where did all 60 lines of `TOOL_SCHEMAS` go? What generates them now?
3. Where did `TOOL_REGISTRY` go?
4. What is `instructions=` in your code?
5. Your loop appended `{"role": "tool", ...}` messages. Who does that now?

Confidence, 1–5: ___

<details>
<summary><b>Open only after you've written all five answers</b></summary>

1. `Runner.run(agent, task, max_turns=10)` — the entire loop, including the exit condition.
2. Generated from each function's **type hints and docstring** by the `@function_tool` decorator. Your `"description"` field is now the docstring; your `"properties"` are now the parameter annotations.
3. Gone — `tools=[...]` on the `Agent` registers name→callable for you.
4. Your `system_prompt`.
5. The SDK, inside `Runner.run`. You never see the message list unless you ask for it (`result.new_items`, `result.to_input_list()`).

</details>

---

## The line-by-line map

| You wrote | The SDK gives you | What it actually does for you |
|---|---|---|
| `for iteration in range(1, MAX_ITERATIONS + 1)` | `Runner.run(agent, input)` | Runs the loop, detects the exit condition, returns a result object |
| `MAX_ITERATIONS = 10` | `max_turns=10` | Same circuit breaker. Raises `MaxTurnsExceeded` instead of returning a string |
| `messages: list[...]` + manual `.append()` | managed internally | Correct assistant/tool message threading, `tool_call_id` wiring |
| `TOOL_SCHEMAS` (60 lines of JSON Schema) | `@function_tool` | Generates the schema from type hints + docstring |
| `TOOL_REGISTRY: dict[str, Callable]` | `tools=[...]` | Name→callable dispatch, plus argument validation before your function body runs |
| `json.loads(tool_call.function.arguments)` | handled | Parsing and type coercion |
| `try/except` around dispatch | handled | Tool exceptions are caught and returned to the model, same as yours |
| `system_prompt=` | `instructions=` | Identical concept |
| `assistant_message.content` | `result.final_output` | The final answer |
| your `AgentRun` + `summary()` | `result.new_items` | The trace of what happened — *(hosted tracing comes in a later chapter)* |
| `client = OpenAI(base_url=...)` | `OpenAIChatCompletionsModel(openai_client=...)` | Same provider swap. The SDK is not tied to OpenAI |

## Three primitives, everything else is a modifier

The whole SDK rests on three things:

```python
Agent(...)        # what it is: instructions + tools + model
Runner.run(...)   # the loop
@function_tool    # a capability
```

Sessions, handoffs, guardrails, tracing, streaming, approvals — every one of them is a **modifier of one of these three**. That single sentence is the map for the rest of this curriculum. When a new SDK feature appears, ask: is it changing the agent, the run, or a tool?

## What the SDK gives you that you did *not* build

Worth being specific, so "just use the SDK" is a decision and not a reflex:

- **Argument validation before your function runs** — a wrong type is rejected and returned to the model, so your function body never sees garbage
- **Parallel tool execution** — you ran them sequentially in a `for` loop
- **Streaming** (`Runner.run_streamed`)
- **A structured item stream** — messages, tool calls, tool outputs, reasoning, handoffs, all typed
- **Hosted tracing**, sessions, guardrails, handoffs — the rest of this curriculum

## What you lost

Honesty matters more than salesmanship:

- **Visibility by default.** Your loop printed every step. The SDK hides them until you go looking in `result.new_items`. When an SDK agent misbehaves, the first move is always to make it visible again.
- **Control of the exit condition.** You decided what "done" meant. Now `max_turns` raises instead of returning your polite budget message, so failure handling is the caller's job.
- **The mental model** — which you now have, and which is the only reason any of the above reads as ordinary code instead of magic.

---

## 🔨 Practice 11 — Break the SDK version the same way you broke yours (10 min)

1. Delete the docstring from `multiply` and run it. What happens to the model's tool choice? (This is Practice 5 all over again — the docstring *is* the description now.)
2. Set `max_turns=1` and run the chained task. Compare the failure to your from-scratch budget message.
3. Change `add`'s parameters to `(a: str, b: str)` and run. Read the error carefully — who caught it, you or the SDK?

**You're done when** you can state which of your hand-rolled protections the SDK kept, and which one it changed the behaviour of.
