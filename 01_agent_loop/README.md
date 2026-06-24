# Step 1 — The Agent Loop

> The single most important pattern in agentic AI. Every framework you've ever heard of — OpenAI Agents SDK, Claude Agent SDK, LangChain, AutoGen, CrewAI — is a different opinion on top of *this* loop.

---

## The Mental Model — A Restaurant Kitchen

Imagine a head chef who can read recipes and decide what to cook, but cannot physically touch anything in the kitchen. They have three cooks they can call out to:

- A **clock cook** who tells them the current time
- An **addition cook** who adds two numbers
- A **multiplication cook** who multiplies two numbers

The chef gets an order, *thinks* about which cook to call, *shouts the request*, the cook does it and *shouts the result back*, the chef *thinks again*, and so on. When the chef has everything they need, they call out "**plate up**" — that's the final answer to the customer.

That's the entire agent loop:

| Kitchen | Agentic loop |
|---|---|
| Order arrives | User message |
| Chef thinks | LLM API call |
| Chef shouts "I need X!" | Tool call in model response |
| Cook does it, shouts result | Tool function executes, result captured |
| Chef sees result, thinks again | Result appended to conversation, next API call |
| "Plate up" — done | Model responds with no tool call → final answer |

The chef is the LLM. The cooks are tools. The shouting back and forth is the loop. **The loop is just `while not done: think → act → observe`.**

---

## The Five Steps in Code

```
1. Send the conversation so far to the LLM.       <- chat.completions.create(...)
2. Parse the model's response.                    <- response.choices[0].message
3. If the response is a tool call, execute it.    <- TOOL_REGISTRY[name](**args)
4. Append the tool result to the conversation.    <- messages.append({"role": "tool", ...})
5. Go to step 1.                                  <- for-loop iteration
```

The loop **exits** when step 2 finds no tool calls in the response — that's the model signaling it's finished.

---

## Files

| File | Purpose |
|------|---------|
| `tools.py` | The three trivial tools + their JSON schemas + the dispatch registry |
| `agent.py` | The agent loop itself — ~80 lines of real code |

---

## Run It

From the project root, with your `.venv` activated and `.env` filled in:

```powershell
cd 01_agent_loop
python agent.py
```

You should see something like:

```
USER TASK:
  What's the current time? Also, calculate 15 multiplied by 7, then add 23 to that result. ...
========================================================================

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
========================================================================

FINAL ANSWER:
The current time is 2026-06-23T14:08:11. 15 multiplied by 7 is 105, and adding 23 gives 128.
```

The exact iteration count and tool ordering will vary because the model decides. **That variation is the entire point of agentic AI** — the system is not a hardcoded pipeline, it's a *decision-maker* with tools.

---

## What to Notice in the Output

1. **The model picked the tools, not you.** No `if/else` in the code says "if the user mentions time, call `get_current_time`." The model decided.
2. **The model chained tool calls.** Iteration 1's `multiply` produced `105`. Iteration 2 used `105` as input to `add`. The model carried the result across turns by reading the conversation history.
3. **Sometimes it calls multiple tools in one turn** (parallel tool calling). Sometimes it goes one at a time. That's the model's choice.
4. **The loop exits on its own.** Nothing in your code says "now stop." The model stops requesting tools, and the loop sees that and exits.

If any of those four points feel surprising, re-read the code with that in mind.

---

## Production Discipline Already Baked In

Even at this primitive stage, three things were not optional:

| Rule | Where it lives |
|------|----------------|
| **Never let the loop run forever** | `MAX_ITERATIONS = 10` |
| **A tool crash must not kill the agent** | `try/except` around the dispatch |
| **API keys never in source** | `.env` + `load_dotenv()` |

These are the bare minimum. We'll add more (cost ceilings, time ceilings, observability hooks) when the failures they prevent show up in later steps.

---

## What's NOT Here Yet (and what we'll add next)

| Missing | Step that adds it |
|---------|-------------------|
| Hand-rolled tool schema + JSON parsing (we use the OpenAI `tools=` shortcut here) | Step 2 |
| Long conversations that exceed the context window | Step 3 |
| Memory across separate runs (right now every run starts fresh) | Step 4 |
| Knowing whether the agent's output was actually correct | Step 5 |
| Refusing dangerous inputs or sanity-checking outputs | Step 6 |

Each of these is a real production failure mode. We'll feel each one before we fix it.

---

## Self-Check Before Moving On

Before you start Step 2, you should be able to answer these three questions **without re-reading the code**:

1. What exactly makes the loop *exit*? Describe the condition.
2. If the model requests a tool that doesn't exist in `TOOL_REGISTRY`, what happens? Trace it through the code.
3. The `messages` list keeps growing every iteration. Why is that necessary? What would break if we sent only the latest message to each API call?

If any answer feels fuzzy, re-read `agent.py` with that question in mind. The loop is small enough that you should *own* it before we add anything on top.

---

## Common Pitfalls (worth knowing now)

- **"My loop runs forever."** Almost always: you forgot to append the tool result to `messages`, so the model keeps re-requesting the same tool because it never saw a result.
- **"The API rejects my next turn."** Almost always: the assistant message with tool_calls wasn't preserved exactly, or the `tool_call_id` on the tool result doesn't match.
- **"The model ignores my tools."** Almost always: the tool description is too vague. Models call tools whose descriptions clearly map to the user's intent.

Each of these is a real bug you will hit. When you do, the fix will be obvious *because* you built the loop from scratch.
