# Chapter 2 — Reference solutions

> **Open these after you attempt, not before.**
>
> Reading a solution feels like learning and is not. If you are stuck for more than 45 minutes on any one thing, read the *smallest* file that unblocks you and go back to your own build.

---

## What is here

| File | What it is | Read it when |
|---|---|---|
| `chapter.py` | The one import shim, explained | First — it is six lines and every other file depends on it |
| `expense_store.py` | The storage layer, carried forward from Chapter 1 with **one** change | You want to see how little had to move |
| `expense_tools.py` | The seven tools, under contract. **The centrepiece.** | After you have written your own version |
| `loop.py` | Chapter 1's loop plus a boundary and a rejection budget | After Practice 8 |
| `expense_agent.py` | System prompt + entry point, from scratch | To see what left the prompt and why |
| `expense_agent_sdk.py` | The same agent on `@function_tool` | After `with_sdk/agent_sdk.py` |
| `test_expense_tools.py` | The adversarial dataset — 46 tests, no API key, ~2s | After Challenge 1, or when you want the shape |
| `check_expenses.py` | The golden dataset — 7 cases, grades **both** builds | After your own harness runs |

---

## Run them

```powershell
# Free, offline, ~2 seconds. Run this constantly.
uv run pytest 02_typed_tools/solutions/ -v

# Costs API calls, ~5 minutes each. Run deliberately.
uv run python 02_typed_tools/solutions/check_expenses.py
uv run python 02_typed_tools/solutions/check_expenses.py --impl sdk

# One run, verbose, to watch the loop think.
uv run python 02_typed_tools/solutions/expense_agent.py
uv run python 02_typed_tools/solutions/expense_agent_sdk.py
```

---

## The five things worth studying, in order

### 1. What left `expense_tools.py`

Diff it against `01_agent_loop/solutions/expense_tools.py`. Roughly 110 lines of hand-written JSON Schema are gone, and so are two of the three guards in `log_expense`.

The guards did not become someone else's problem. They moved into the signature, where they do three jobs instead of one: they tell the model, they check the input, and they inform your type checker.

### 2. The one guard that stayed

```python
if when > date.today().isoformat():
    raise ToolError(...)
```

"Not in the future" is a comparison against the clock at call time. No JSON Schema can hold it.

**Types hold shape, range and membership. They do not hold rules that depend on the world.** Knowing exactly where that line falls is the difference between using types well and expecting them to save you.

### 3. Two bugs the tests found

Both are commented in place, and neither was theoretical:

- **`amount: true` was accepted as `1.0`.** `bool` subclasses `int`, so Pydantic's lax mode takes it. Fixed with a `BeforeValidator`, which is the only place the check can live — after float coercion, `True` is already `1.0`.
- **That fix silently broke the schema.** With a custom validator attached, Pydantic stopped translating `gt=0` into JSON Schema's `exclusiveMinimum` and emitted the raw `"gt": 0` instead. Not a JSON Schema keyword, so the model never learned the constraint. Nothing crashed. The agent just paid for a round trip on a rule it thought it had published. Fixed by `_clean_schema` in `typed_tool.py`.

> The second one is the more instructive. It is the failure mode this chapter is about, one level up: **the code was right and the contract was wrong.** That is why `test_expense_tools.py` asserts on schemas and not only on behaviour.

### 4. The prompt lines that came back

`expense_agent.py` opens with a mistake and its correction. Short version: two Chapter 1 prompt rules were deleted because `Literal` and `Field(gt=0)` "already enforce them", and the golden dataset failed three cases on the SDK build:

```
"Log -450 at Imtiaz Supermarket for groceries."
  -> "I have successfully logged your expense of PKR 450.00."
```

`gt=0` worked. No negative number reached the tool. **The model flipped the sign before calling**, so the boundary saw a clean, valid, fabricated `450`.

> **A type stops a bad value from being accepted. It does not stop the model from manufacturing a good one.**

The type made the enforcement redundant; it did not make the policy redundant. Both rules are back, marked, with the failing output recorded above them.

### 5. The `executed_names` hack in the SDK build

Our loop catches `ToolError`, so it knows precisely which calls never reached a function body.

The SDK swallows the failure and returns your error string as the tool output — so from the outside a rejected call and a successful one are indistinguishable. `expense_agent_sdk.py` recovers the fact by matching the prefix of a message it wrote itself.

That is a hack, it is left in deliberately, and it is worth sitting with: **an abstraction that handles an event for you also decides how much of that event you may see afterwards.**

---

## Still superseded from Chapter 1

Nothing in this folder replaces anything in `01_agent_loop/solutions/`. Chapter 1's files stay where they are — the diff between the two chapters is a teaching artefact in its own right.
