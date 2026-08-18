# Our code → the SDK — Chapter 4

Chapter 1 built a message list by hand. Chapter 4 does not rebuild it, because there is
nothing left to learn from rebuilding it. This file is the map between the two.

---

## The message list

| Chapter 1, `from_scratch/agent.py` | Chapter 4 | What the SDK does for you |
|---|---|---|
| `messages: list[dict] = []` | `SQLiteSession(session_id)` | Storage, with a durable backing store instead of a variable |
| `messages.append({"role": "user", ...})` | `session=session` on `Runner.run` | Appends the user turn before the run, the assistant turn after |
| `messages.append(tool_result_message)` | — | Tool calls and their results are appended as separate items, correctly paired |
| `messages` passed to the next call | — | Loaded and prepended automatically |
| *(nothing)* | `session.get_items()` | Read the transcript back |
| *(nothing)* | `session.add_items(...)` | Inject turns that never happened |
| *(nothing)* | `session.pop_item()` | Remove the newest item |
| *(nothing)* | `session.clear_session()` | Empty without deleting the DB |

**The stored shape is identical.** Print `session.get_items()` and compare it with the
list you built in Chapter 1 — same roles, same tool-call pairing, same append-only growth.
`session_demo.py` PART 2 prints both facts on purpose.

---

## The context object

There is no Chapter 1–3 equivalent. It is a genuinely new primitive.

| What you would have written | Chapter 4 | Why the SDK version is better |
|---|---|---|
| A module-level `MONTHLY_BUDGETS` dict | `ctx.context.budgets` | Works for two users |
| `f"The user's budget is {budget}"` in the prompt | `RunContextWrapper[User]` | Not tokens, not visible to the model, not roundable |
| A global `current_user` | `context=user` on `Runner.run` | Concurrent requests do not fight |
| Passing `user` through every function | first parameter, injected | The model never sees it in a schema |

```python
@function_tool
def get_budget(ctx: RunContextWrapper[User], category: Category) -> float:
    return ctx.context.budget_for(category)
```

The SDK strips a leading `RunContextWrapper` before generating the tool schema. Verify it
rather than believing it — `context_demo.py` PART 1 prints the schemas and costs nothing.

---

## What does NOT transfer

Three things the SDK does not do, which you will otherwise assume it does.

**1. It does not scope the session for you.** `session_id` is an unvalidated string, and
`db_path` defaults to `":memory:"`. Two objects with the same id and different paths are
two different conversations, silently. Two conversations with the same id and the same
path are one conversation, silently. Both are your problem.

**2. It does not prune.** `SQLiteSession` appends forever. `SessionSettings(limit=N)` and
`get_items(limit=N)` cap what you **read**, never what you **store**, and they count items
rather than tokens — so they can slice a `function_call` away from its
`function_call_output`. That is Chapter 5.

**3. It does not keep the model honest about what it remembers.** A session makes stale
recital *possible*; nothing in the SDK makes it *unlikely*. That stays a prompt rule
backed by an assertion in your dataset — README §8, dataset case M4.

---

## Two lines that carry the whole chapter

```python
result = await Runner.run(agent, prompt, session=session, context=user)
#                                        ^^^^^^^^^^^^^^^  ^^^^^^^^^^^^
#                                        what it remembers  what you hand it
```
