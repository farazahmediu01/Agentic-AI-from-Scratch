# Chapter 2 — our code → the SDK, line by line

> Read this **after** `from_scratch/typed_tool.py` makes sense. It is a map, not a tutorial.

---

## The one-line summary

`@function_tool` **is** `typed_tool.py`. Same three moves, same conclusions, one third of the code, and one default you should override.

---

## The mechanism

| We wrote | The SDK | Notes |
|---|---|---|
| `@tool` | `@function_tool` | Both read the signature and build a Pydantic model from it |
| `inspect.signature(fn)` | `agents.function_schema.function_schema()` | Same call, more edge cases handled (varargs, `RunContextWrapper` first arg) |
| `create_model(...)` | `create_model(...)` | Genuinely the same Pydantic function |
| `args_model.model_json_schema()` | `schema.params_json_schema` | Same |
| `inspect.getdoc(fn)` as the description | the docstring, parsed | The SDK goes further: it reads `griffe`-style param docs and puts them on individual fields |
| `ConfigDict(extra="forbid")` | `additionalProperties: false` | Same decision, reached independently |
| `Tool.call(raw)` | `FunctionTool.on_invoke_tool(ctx, raw)` | parse → validate → dispatch, identical order |
| `json.loads` then `model_validate` | `json.loads` then `params_pydantic_model(**data)` | Identical |
| `ToolError` | `ModelBehaviorError` + `failure_error_function` | See below — this is the interesting row |
| `explain(name, exc)` | `default_tool_error_function` | Ours is better. See below |
| `registry(tools)` / `schemas(tools)` | `tools=[...]` on the `Agent` | The list is the registry |
| `Tool.parameters` | `tool.params_json_schema` | For inspecting the contract in tests |
| `MAX_INVALID_CALLS` | **nothing** | The SDK has no rejection budget. See "does not transfer" |
| *(nothing)* | `strict_json_schema=True` | Provider-side constrained decoding — a layer below us |

---

## 🔒 The row that matters: error text

Out of the box, this is the entire message a model receives when its arguments are rejected:

```
Invalid JSON input for tool add.
```

Ours, from the identical failure:

```
INVALID ARGUMENTS for tool 'add'. Nothing was executed.
  - a: Input should be a valid number, unable to parse string as a number (you sent: 'fifty')
Fix the arguments and call 'add' again. If the correct value is something the
user never told you, ask them for it. Do not invent it.
```

### Why the SDK's is short

Not laziness. `agents/_debug.py`:

```python
DONT_LOG_TOOL_DATA = _debug_flag_enabled("OPENAI_AGENTS_DONT_LOG_TOOL_DATA", default=True)
```

Tool arguments routinely carry personal data — amounts, emails, addresses, medical details. Echoing them into error strings, logs and traces **by default** would be a privacy incident waiting for its first enterprise customer. So the SDK defaults to saying nothing, and the detail is opt-in.

That is a defensible default. It is also **a decision about your tradeoffs, made without you.**

### The two ways to get the detail back

```powershell
# 1. globally, via the environment
OPENAI_AGENTS_DONT_LOG_TOOL_DATA=0
```

```python
# 2. per tool, via the hook — this is the one to reach for
@function_tool(failure_error_function=explain_to_model)
def add(a: float, b: float) -> float: ...
```

Option 2 is better because the tradeoff is **per tool**, not per application. Be verbose for `add`. Be silent for `charge_credit_card`. A global flag cannot express that; `failure_error_function` can.

`explain_to_model` in `agent_sdk.py` is `typed_tool.explain()` with one extra step: the SDK wraps validation failures in `ModelBehaviorError`, so the original `ValidationError` lives on `error.__cause__`.

---

## 🔒 What does **not** transfer

### 1. There is no rejection budget

Our loop counts rejected calls and stops at `MAX_INVALID_CALLS`. The SDK counts **turns** (`max_turns`) and nothing else.

Those are not the same budget:

| | bounds | fails when |
|---|---|---|
| `max_turns` | how *long* the agent talks | a task legitimately needs many steps |
| `MAX_INVALID_CALLS` | how *wrong* it is allowed to be | the model cannot read a contract |

An SDK agent stuck re-sending the same invalid argument will spin until `max_turns`, paying for every lap. If you want it to stop sooner, you build that yourself — with a counter in `RunHooks`, or a context object, or a guardrail. Nothing ships with it.

### 2. You lose the ability to tell "called" from "executed"

Our loop catches `ToolError`, so it knows exactly which calls never reached a function body — hence `AgentRun.executed_names`.

The SDK **swallows** the failure and returns your error string as the tool's output. From the outside, a rejected call and a successful one look the same: a `ToolCallItem` followed by a `ToolCallOutputItem`. The only way back to the fact is to recognise the string you wrote yourself — which is what `REJECTED_PREFIX` in `solutions/expense_agent_sdk.py` does, and it is a hack.

> **An abstraction that handles an event for you also decides how much of that event you may see afterwards.** That is the recurring cost of frameworks, and it is worth naming every time you meet it rather than discovering it during an incident.

### 3. Rules that depend on the world are still yours

`log_expense` refuses a date in the future. No schema can express that — it is a comparison against the clock at call time. `@function_tool` does not help, `strict` does not help, and no amount of typing removes it.

Types hold **shape, range, membership**. They do not hold **state**: today's date, the account balance, whether this user is permitted to spend. Those stay hand-written, in the body, raising a recoverable error.

---

## What the SDK adds that we did not build

| | Why it matters |
|---|---|
| `strict_json_schema=True` | Asks the *provider* to constrain generation to the schema. Many invalid calls are never emitted at all. Not universal — Gemini's compatibility endpoint is not OpenAI — so it supplements your validation, never replaces it |
| Docstring param parsing | `griffe` reads `Args:` sections and attaches descriptions to individual fields. We put the whole docstring in one blob |
| `RunContextWrapper` as an optional first argument | Per-run dependencies injected into tools. A whole chapter of its own, later |
| Parallel tool execution | We run rejections and executions sequentially |
| `is_enabled=` | Tools that appear and disappear based on run state — a Trust primitive we have not met yet |

---

## The sentence for this chapter

> *"I built the mechanism that turns a signature into a validated tool contract. The SDK does it with `@function_tool`. What it does for me is the boilerplate — schema generation, parsing, validation, dispatch, plus provider-side strict decoding I could not build. What it decides for me that I should check is how much a rejected call is allowed to tell the model."*
