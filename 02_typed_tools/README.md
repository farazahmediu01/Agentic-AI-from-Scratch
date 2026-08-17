# Chapter 2 — Typed Tools

> **Axes:** 🔒 **Trust** (primary) · 📐 Proof (secondary)
>
> **You built:** an agent that can call your functions.
> **You will build:** an agent that cannot call them *wrongly*.

| Part | Core | Full |
|---|---|---|
| This README (§1–§11) | 5.75 hrs | 7.75 hrs |
| [`EXERCISES.md`](EXERCISES.md) — Track 1️⃣ drills | 2 hrs | 6–8 hrs |
| [`PROJECT.md`](PROJECT.md) — Tracks 2️⃣ + 3️⃣ | 3.5 hrs | 4.5 hrs |
| **Chapter total** | **≈ 11.25 hrs** | **≈ 18–20 hrs** |

**Plan 3 sessions.** Every section below is marked `[core]` or `[depth]` and carries its own estimate; the numbers above are the sum of those estimates. If they ever disagree, the header is the bug — tell us.

Finish the **core** column and you are ready for Chapter 3 with nothing missing.

> ### 📖 What `[depth]` means, and why it exists
>
> The `[depth]` blocks in this chapter are mostly about **how the machinery is built** — reading `inspect.signature`, `create_model`, and JSON Schema generation. That is genuinely interesting metaprogramming and it is genuinely optional.
>
> It is optional because the skill this chapter is actually for is *"I can define a tool the model cannot call wrongly, and I can tell when the contract I published is wrong."* You get that from **using** the decorator and from reading the failures. You do not get it from writing the decorator.
>
> An earlier version of this chapter had you rebuild the decorator from an empty file. It took 60–90 minutes, and the students who finished it could write Python metaprogramming — not agents. Skip the depth blocks the first time through. Come back for them when you're curious, or when you need to debug one.

---

## Before you start

You need Chapter 1 finished and running. This chapter edits that code rather than replacing it.

```powershell
uv sync
uv run python 01_agent_loop/from_scratch/agent.py   # should still work
```

Every file in this chapter is checked by the same gate you will use for the rest of the curriculum:

```powershell
uv run ruff format .        # style
uv run ruff check .         # lint
uv run pyright              # types
uv run pytest               # proof
```

Run all four before you call any exercise finished. "It works on my machine" is not a completion criterion.

---

## 1. The question this chapter answers `[core]` · 15 min

Chapter 1 ended with a working agent. Here is the line that made it work:

```python
tool_fn = TOOL_REGISTRY[tool_name]
tool_result = tool_fn(**tool_args)
```

Read it again as a **security** question rather than a plumbing question.

`tool_args` is a dict that a language model wrote. `**` unpacks it directly into your function's parameters. There is nothing in between — no check on the names, no check on the types, no check on the values. A token predictor writes a JSON string and your code executes it.

We would never write this against a web form. It is the classic un-validated boundary, and we built one on purpose in Chapter 1 because you cannot appreciate the fix until you have felt the hole.

> ### 🧠 Mental model: the tool call is a network request from a stranger
>
> You already know how to think about this. When a browser POSTs to your API, you do not trust the body. You do not assume `amount` is a number. You do not assume the fields you asked for are the fields you got. You validate at the door, reject with a clear message, and only then run your logic.
>
> A tool call is that same POST. The stranger is the model. It is usually well-behaved, occasionally confused, and always — structurally — capable of sending you anything.
>
> The rest of this chapter is one idea: **move the checking to the door.**

### ▶ Practice 1 — predict, then look (5 min)

Do not run anything yet. For each of these payloads, write down what you think Chapter 1's agent does — crash, error message, or something else:

| # | The model sends | Your prediction |
|---|---|---|
| 1 | `add({"a": "fifty", "b": 3})` | |
| 2 | `add({"a": 5})` | |
| 3 | `add({"a": 5, "b": 3, "precision": 2})` | |
| 4 | `log_expense({..., "category": "astrology"})` | |
| 5 | `add({"a": "5", "b": "3"})` | |

Rank them from most dangerous to least dangerous.

**You're done when:** you have five written predictions and a ranking. Keep the paper — you will check it in Practice 2.

---

## 2. Watch it break `[core]` · 20 min

```powershell
uv run python 02_typed_tools/from_scratch/break_it.py
```

No API key needed. The file dispatches those exact payloads through Chapter 1's dispatch code and prints what the model would have been told.

Four of the six raise. **Two do not**, and those two are the reason this chapter exists:

```
add(a="5", b="3")            ->  "53"
log_expense(...,"astrology") ->  WROTE TO LEDGER
```

Python concatenated two strings and handed `"53"` back as the sum of five and three. A category that does not exist was written to permanent storage, and the model was told it succeeded.

> **The failures that hurt are the ones that do not raise.**
>
> A crash is loud, local and debuggable. A silently wrong value propagates through the rest of the conversation, gets reasoned on, and arrives at the user wearing a full sentence of justification. A silently wrong *write* is still there tomorrow.

Now look at the four that did raise, and ask the second question of this chapter — **could the model do anything with what we told it?**

```
ERROR: TypeError: can only concatenate str (not "int") to str
```

That message names a Python internal. It does not name the tool. It does not say which argument was wrong. It does not say what shape was expected. It does not say whether anything was already written. It is a message for a developer reading a traceback, and **there is no developer here.** The only reader is a model deciding what to do next.

### ▶ Practice 2 — score your predictions (10 min)

Compare the output against your Practice 1 sheet.

1. Which ones did you get wrong?
2. Most people rank "wrong type" as most dangerous and "numeric strings" as harmless. Why is that backwards?
3. Add a seventh payload to `ATTACKS` that you think is worse than any of the six. Run it. Were you right?

<details>
<summary>Spoiler — one answer worth having</summary>

The danger is not proportional to how *broken* something looks. It is proportional to **how far the wrongness travels before anyone notices.** An exception travels zero distance. A `"53"` travels the whole rest of the conversation. A bad ledger row travels until someone reads their spending report next month.

</details>

**You're done when:** you can say in one sentence why an exception is a *better* outcome than a returned value.

---

## 3. Do it by hand first `[core]` · 25 min

The obvious fix is to check the arguments yourself. So here is that fix, written out once, properly, for a single tool.

**Read this file. Do not write it.** Its whole job is to present you with a bill.

```powershell
uv run python 02_typed_tools/from_scratch/handrolled.py
```

Read the file before you read its output. It enforces seven rules on `log_expense(vendor, amount, category)`:

1. the payload is an object
2. no unknown keys
3. `vendor` present, string, not blank
4. `amount` present, numeric, **not a bool**, greater than zero
5. `category` present, string, one of ten
6. `expense_date` optional, `YYYY-MM-DD` if present
7. every message written for the model, not for a developer

It works. Every attack from §2 is now caught, including both silent ones. **That is not the problem.** The problem is the bill:

```
~85 lines of validation, for ONE tool with THREE arguments.
Spendly Lite has seven tools.
A real agent has thirty.
```

And the true cost is worse than the line count, because that code duplicates a fact that already exists twice:

| Where | How it says "amount is a number" |
|---|---|
| the function signature | `amount: float` |
| the hand-written JSON Schema | `"amount": {"type": "number"}` |
| `validate_log_expense` | `isinstance(amount, (int, float))` |

**Three copies of one fact, kept in sync by hope.** The first person to add a `notes` parameter will update one or two of them.

> Notice rule 4's bool check. In Python `bool` is a subclass of `int`, so `isinstance(True, int)` is `True` and an expense of `PKR 1.00` gets logged when the model answers `{"amount": true}`. Keep that in mind — it comes back in §6 and it bites there too.

### ▶ Practice 3 — extend the gauntlet (15 min)

Add an eighth rule to `validate_log_expense`: **`amount` must not exceed 1,000,000.**

Then answer, in a comment above your new code:

- how many lines did it take?
- how many *other* places now need the same change so the model finds out about the limit?

**You're done when:** the rule is enforced, and you have written down the number of places the rule now lives.

---

## 4. One declaration, three outputs `[core]` · 20 min

So the goal is not "add validation" — you just read one, and it does not scale. The goal is:

> **One declaration that produces the signature, the schema the model reads, and the check on the way in.**

Python already has the declaration. It is the type hint you were writing anyway.

```python
def log_expense(vendor: str, amount: float, category: Category) -> str: ...
```

The move is to stop treating that line as documentation.

> ### 🧠 Mental model: in agentic Python, type hints are executable
>
> In ordinary Python, `amount: float` is a note to the next human and to your type checker. It does nothing at runtime.
>
> In agentic Python it does three things:
>
> | It becomes | Which means |
> |---|---|
> | `"type": "number"` in the JSON Schema | the model is *told* the contract before it calls |
> | a runtime check at the boundary | a bad call is stopped *before* your body runs |
> | a fact `pyright` can see | your own bugs are caught at edit time |
>
> This is the single most important shift in the chapter. It is also why the SDK, FastAPI, and every serious modern Python tool converged on the same trick: read the annotations, generate everything else.

So `from_scratch/typed_tool.py` gives you a decorator that does it:

```python
@tool
def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b
```

That one declaration now produces all three artefacts. The validator and the schema are built from the *same* source, which means **they cannot disagree** — and that is the entire design. Three copies kept in sync by hope became one copy that cannot drift.

> **You are not going to write this decorator.** `@tool` exists here so you can see what the SDK's `@function_tool` is, in code short enough to read in one sitting. In §10 you will switch to the SDK's version and never hand-roll it again. If you want to know how it is built, §4b has it — that block is optional, and deliberately so.

### ▶ Practice 4 — generate a schema (15 min)

```powershell
cd 02_typed_tools/from_scratch
uv run python -c "import json; from tools import add; print(json.dumps(add.schema, indent=2))"
```

1. Compare it, key for key, with the hand-written schema for `add` in `01_agent_loop/from_scratch/tools.py`. What is in one and not the other?
2. Delete `add`'s docstring and run it again. What happens, and why is that the right behaviour?
3. Change `a: float` to `a: int` and diff the schema.

**You're done when:** you can name, for every key in the generated schema, **which part of the function declaration produced it** — the name, the annotation, the default, or the docstring.

---

## 4b. How `tool()` builds it `[depth]` · 30 min

*Skip this on a first pass. Nothing later in the chapter depends on it.*

Open `from_scratch/typed_tool.py` and read `tool()`. About thirty lines, three moves:

```python
signature = inspect.signature(fn)           # 1. what arguments exist
args_model = create_model(..., **fields)    # 2. build a validator
schema = args_model.model_json_schema()     # 3. publish the contract
```

The details worth having if you ever need to debug a generated schema:

- **`get_type_hints(fn, include_extras=True)`** — without `include_extras`, `Annotated[float, Field(gt=0)]` silently collapses to plain `float` and every constraint you wrote vanishes. This is the single most common way a generated schema loses information.
- **`create_model(name, __config__=ConfigDict(extra="forbid"), **fields)`** — `fields` maps each parameter to `(annotation, default)`, with `...` marking required. `extra="forbid"` is what becomes `additionalProperties: false`.
- **`_clean_schema()`** — strips Pydantic's `title` keys and renames constraint names Pydantic emits raw. See §6; that rename exists because of a real bug.

### ▶ Practice 4b — break the extraction (15 min) `[depth]`

In `typed_tool.py`, change `get_type_hints(fn, include_extras=True)` to drop the `include_extras` argument. Regenerate `log_expense`'s schema.

**You're done when:** you can state exactly which keys disappeared, and why the tool still *works* while the model is now less likely to call it correctly.

---

## 5. Closed sets: `Literal` `[core]` · 20 min

Chapter 1 had ten expense categories and could only ask for them in English:

```python
"description": "One of exactly these categories: Food & Dining, Transportation, ..."
```

That is a **request**. The model usually honours it. "Usually" is doing a lot of work in a system that writes to a ledger.

```python
Category = Literal["Food & Dining", "Transportation", ...]

def log_expense(..., category: Category) -> str: ...
```

Now the closed set is in the type, so it appears in the schema as a real `enum`, and an invalid value is rejected before the body runs:

```json
"category": { "type": "string", "enum": ["Food & Dining", "Transportation", ...] }
```

> **`Literal` is the sleeper feature of typed tools.** Most tool arguments that cause real damage are not free-form — they are one of N: a status, a currency, an account type, a permission level. Every one of those you can express as a `Literal` is a class of wrong call that stops being possible.

Look at how `02_typed_tools/solutions/expense_store.py` does it:

```python
Category = Literal["Food & Dining", ...]
CATEGORIES: tuple[str, ...] = get_args(Category)   # derived, not retyped
```

One source of truth. The runtime tuple comes *from* the type. Two hand-maintained copies of the same list is exactly the drift this chapter deletes.

### ▶ Practice 5 — close a set (10 min)

In `from_scratch/tools.py`, `convert_temperature` already uses `Literal`. Add a new tool of your own with a closed set — for example `round_amount(value: float, mode: Literal["up", "down", "nearest"])`.

Then break it deliberately:

```python
round_amount.call('{"value": 1.5, "mode": "UP"}')
```

**You're done when:** the tool exists, the enum appears in `round_amount.schema`, and you can quote the rejection message for `"UP"`.

### ⚡ Challenge 5b — should `"UP"` be rejected? `[depth]` · 20 min

`"UP"` is obviously what the user meant. Strictness rejected it; a `BeforeValidator` that lowercases first would accept it.

Argue both sides in three sentences each, then pick one and implement it. There is a defensible answer either way — what is not defensible is not knowing you made the choice.

---

## 6. Ranges, formats, and the defaults you did not choose `[core]` · 25 min

`Literal` handles membership. `Annotated` + `Field` handles everything else:

```python
Amount = Annotated[float, Field(gt=0, description="Amount in PKR. Must be greater than zero.")]
IsoDate = Annotated[str, Field(pattern=r"^(\d{4}-\d{2}-\d{2})?$")]
Limit   = Annotated[int, Field(ge=1, le=50)]
```

Naming them matters. `vendor: Vendor` reads as a domain concept; the raw `Annotated[...]` inline reads as plumbing, and a signature made of plumbing is unreadable at seven arguments.

But here is the part you must not skip. **A validation library has defaults, and the defaults are somebody else's judgement.**

```python
class M(BaseModel):
    x: float

M(x=True)   # -> x=1.0
```

`bool` is a subclass of `int`, so Pydantic's default lax mode happily accepts `true` as a number — the same trap the hand-rolled gauntlet had to check for by hand in §3. A model that answers `{"amount": true}` logs an expense of PKR 1.00.

`02_typed_tools/solutions/expense_tools.py` fixes it with a `BeforeValidator`, which runs *ahead* of coercion — the only place the check can live, because after float parsing `True` is already `1.0` and indistinguishable from a real amount.

> **This was found by a test, not by reading.** `test_expense_tools.py` had `amount as a boolean` in its attack list and it failed on the first run. Then the fix caused a *second*, quieter bug — adding a validator made Pydantic emit `"gt": 0` instead of JSON Schema's `"exclusiveMinimum"`, so the constraint silently stopped reaching the model. Nothing crashed. The agent just paid for an extra round trip on a rule it thought it had published.
>
> Both are in the code with comments. Neither was theoretical.

### ▶ Practice 6 — meet the bool trap yourself (10 min)

Temporarily delete `BeforeValidator(_reject_bool)` from `Amount` in `solutions/expense_tools.py`, then:

```powershell
uv run pytest 02_typed_tools/solutions/ -k boolean -v
```

1. Read the failure.
2. Put it back and watch it pass.
3. Now delete the `_JSON_SCHEMA_NAMES` rename in `typed_tool.py` and run `uv run pytest 02_typed_tools/solutions/ -k leak -v`.

**You're done when:** you have seen both tests fail and both pass, and can explain why the second bug is more dangerous than the first even though it breaks nothing.

---

## 7. Errors as instructions `[core]` · 20 min

A boundary that only says "no" costs you a turn. A boundary that says "no, **and here is the shape**" costs you a turn and buys a correct call.

Compare the same failure, three ways:

| Audience | The message |
|---|---|
| Chapter 1 | `ERROR: TypeError: can only concatenate str (not "int") to str` |
| Pydantic raw | `1 validation error for AddArgs / a: Input should be a valid number` |
| `explain()` | `INVALID ARGUMENTS for tool 'add'. Nothing was executed.`<br>`  - a: Input should be a valid number (you sent: 'fifty')`<br>`Fix the arguments and call 'add' again. If the correct value is something the user never told you, ask them for it. Do not invent it.` |

The third one names the tool, states that nothing happened, echoes what was actually sent, and says what to do next — including the case that causes the most damage in practice: **when the right value is one the user never gave you.**

> **Error messages inside an agent are not diagnostics. They are instructions.**

There is a second decision hiding here, and it is the more important one:

```python
class ToolError(Exception):
    """A failure the model is expected to read and act on."""
```

Two kinds of failure live inside an agent and they belong to different owners:

| Kind | Owner | What to do |
|---|---|---|
| Bad arguments, invalid category, business rule violated | **the model** | put it in the conversation, let it try again |
| 429, dead database, bug in your tool | **you** | tell the model it cannot fix this, stop the retry loop |

Ask it of every error you raise: **can the model do something about this?** Handing a model a `ConnectionError` just burns turns while it invents workarounds for a problem it cannot see.

### ▶ Practice 7 — rewrite a bad error (10 min)

`from_scratch/tools.py` has `divide`, which raises `ToolError` on `b == 0`. Change it to raise a plain `ZeroDivisionError` instead, run the agent with a task that divides by zero, and read what comes back. Then restore it.

**You're done when:** you can state which of the two messages a model could act on, and why.

---

### 7b. A type stops a bad value. It does not stop an *invented* one. `[core]` · 20 min

This is the most important paragraph in the chapter, and it was learned the expensive way — by shipping the mistake and having the golden dataset catch it.

The first draft of Spendly Lite v2 deleted two lines from Chapter 1's system prompt:

```
"Categories are a fixed set. Never invent one."
"Never log a negative or zero amount. Do NOT correct the value yourself."
```

The reasoning sounded airtight. Those are shape rules. `Literal` and `Field(gt=0)` now enforce them at the boundary. Why ask the model politely for something the type guarantees?

Then the dataset ran, and the SDK build failed:

```
CASE 5  "Log -450 at Imtiaz Supermarket for groceries."
        -> "I have successfully logged your expense of PKR 450.00."

CASE 7  "Log 3000 at Metro for groceries on 2099-01-01."
        -> rejected once for the future date, then re-called with TODAY,
           and reported success.
```

**Neither is a validation failure.** `gt=0` worked perfectly — no negative number ever reached the tool. The model flipped the sign *before* calling, and the boundary saw a clean, valid, completely fabricated `450`.

Case 7 is sharper still. The rejection message *literally says* "if the correct value is something the user never told you, ask them for it. Do not invent it." The model read that and substituted today's date anyway.

> | | stops | does not stop |
> |---|---|---|
> | **A type** | a bad value being **accepted** | the model **manufacturing** a good one |
> | **A prompt** | the model manufacturing a good one | anything, reliably, on its own |
>
> They defend against different things and neither substitutes for the other. The type made the *enforcement* redundant. It did not make the *policy* redundant.

The deleted lines are back in `solutions/expense_agent.py`, marked, with the failure recorded above them.

### ⚡ Challenge 7c — reproduce it `[depth]` · 30 min

Delete the `NEVER SILENTLY CORRECT THE USER'S DATA` block from `SYSTEM_PROMPT` and run case 5 alone:

```powershell
uv run python -c "
import sys; sys.path.insert(0, '02_typed_tools/solutions')
from check_expenses import CASES, run_with_sdk
import expense_store; expense_store.reset(seeded=True)
run = run_with_sdk(CASES[4].prompt)
print(run.final_answer)
print([r['amount'] for r in expense_store.all_expenses() if r['notes'] != 'seed'])
"
```

Then answer the question that actually matters: **a prompt rule is not a guarantee either.** The model can ignore it, and on some runs it will. So where does a guarantee against this class of failure have to live, if not in the type and not in the prompt?

<details>
<summary>The answer, which is also the shape of Chapter 6</summary>

Outside the model. A check that runs *after* the tool call and *before* the write — comparing what the user said against what the tool was asked to do — is the only thing that cannot be talked out of its job. That is a guardrail, and this is why guardrails exist as a separate primitive rather than a longer prompt.

Notice the progression the curriculum is walking: **prose → type → boundary → guardrail.** Each step moves enforcement further from persuasion and closer to code.

</details>

---

## 8. The loop learns to recover `[core]` · 30 min

With a boundary in place, the loop gains one branch — and the branch is the point of the whole chapter.

Open `from_scratch/agent.py` and diff it against Chapter 1's. Three changes:

```python
try:
    result = tool.call(raw)          # parse -> validate -> dispatch
except ToolError as exc:
    invalid_calls += 1
    result = str(exc)                # the model's problem: hand it back
except Exception:
    result = "...failed internally, you cannot fix this..."   # ours
```

A rejected call is **not** a crash. It is data in the conversation, and the model gets another turn. Chapter 1's agent could fail; this one can **recover**.

Which immediately raises a budget question, and therefore a second circuit breaker:

```python
MAX_INVALID_CALLS = 3
```

Without a ceiling, a model that has decided a parameter exists will send it, read the rejection, apologise, and send it again — a polite infinite loop costing a request per lap. Set the ceiling **above** the number of retries a correct recovery needs, not at it: one rejection followed by a fixed call is healthy behaviour and must not trip the breaker.

> `MAX_ITERATIONS` bounds how *long* the agent talks. `MAX_INVALID_CALLS` bounds how *wrong* it is allowed to be. They are different budgets and they fail differently.

### ▶ Practice 8 — force a recovery (15 min)

Run the from-scratch agent with a task designed to get rejected first:

```powershell
uv run python 02_typed_tools/solutions/expense_agent.py
```

then edit `TASK` to `"Log 1200 at Careem for transportation on 05/08/2026 (the 5th of August)."` and run it again.

1. Did the model send `05/08/2026` and get rejected?
2. Did it fix the date on the next turn?
3. Set `MAX_INVALID_CALLS = 1` and run again. What changes?

**You're done when:** you have one run in your terminal showing a rejection followed by a successful call.

### ⚡ Challenge 8b — the distinction Chapter 1 could not draw `[depth]` · 10 min

`loop.py` has both `tool_names` and `executed_names`. Explain, in two sentences, why an eval that asserts `"log_expense" in run.tool_names` is now **wrong**, and what it should assert instead.

---

## 9. Test the boundary, not the agent `[core]` · 30 min

Here is the structural payoff, and it is bigger than the validation.

The tool boundary is now a **pure function of a JSON string**. `Tool.call('{"amount": -450, ...}')` needs no model, no network, no key. So it can be attacked directly — thousands of times, in milliseconds, for free.

```powershell
uv run pytest 02_typed_tools/solutions/ -v
```

46 tests. About two seconds. Zero cost.

Chapter 1 could not have this file. Its validation lived inside function bodies that touched storage, so testing "is a bad category rejected?" meant writing to a JSON file and cleaning up after.

> **The rule this establishes, for the rest of the curriculum:**
>
> | Question | Where it belongs |
> |---|---|
> | Is a negative amount rejected? Is `'astrology'` rejected? | `pytest` — a property of the boundary, free |
> | Did the agent ask instead of guessing? Did it recover? | the golden dataset — needs a model, costs minutes |
>
> Push every assertion you can down to the boundary. Spend model calls only on what genuinely needs a model.

And note what `test_expense_tools.py` asserts *besides* behaviour — it asserts on the **schema**:

```python
def test_category_enum_reaches_the_schema() -> None:
    enum = log_expense.parameters["properties"]["category"]["enum"]
    assert set(enum) == set(CATEGORIES)
```

A tool can behave perfectly and still be broken, if the contract it published to the model was wrong. That is exactly the `"gt"` bug from §6, and this is the shape of test that catches it.

### ▶ Practice 9 — add three attacks (15 min)

Add three payloads to the `ATTACKS` list that are not there yet. Ideas: a `null` where a string belongs, a nested object where a number belongs, a category with a trailing space, a `vendor` 10,000 characters long.

**You're done when:** `uv run pytest 02_typed_tools/solutions/` is green with your three new cases, and at least one of them made you change `expense_tools.py`.

---

## ✅ Checkpoint 1

Before the SDK layer, you should be able to answer these without looking:

1. Why is `add(a="5", b="3") -> "53"` worse than `add(a="fifty", b=3) -> TypeError`?
2. What are the three artefacts `@tool` produces from one signature?
3. What is the difference between `ToolError` and every other exception, and who owns each?
4. Why does `MAX_INVALID_CALLS` need to be greater than 1?
5. Name one rule that a type **cannot** hold, and say where it has to live instead.
6. `Field(gt=0)` is in place and no negative number can reach `log_expense`. Explain how the ledger still ends up with a fabricated `450.00` in it.

<details>
<summary>Answer to 5, since it is the one people miss</summary>

"The date is not in the future." It is a comparison against the clock, evaluated at call time — no JSON Schema can express it, so it stays a hand-written guard inside `log_expense`. Types hold **shape, range and membership**. They do not hold rules that depend on the world: today's date, the account balance, whether this user is allowed to spend.

Knowing where that line is drawn is the difference between using types well and believing they will save you.

</details>

---

## 10. Now the SDK `[core]` · 90 min — **the longest section, and the point of the chapter**

Everything up to here was scaffolding. From this section onward, in this chapter and every chapter after it, **`@function_tool` is how you define a tool.** You will not hand-roll another one.

```powershell
uv run python 02_typed_tools/with_sdk/agent_sdk.py
```

`@function_tool` is `typed_tool.py`. Same three moves — read the signature, build a Pydantic validator, generate the schema — and it reaches the same conclusions, down to `additionalProperties: false`.

So the interesting part is not what it does the same. It is the one default it sets differently, and *why*.

Out of the box, a rejected tool call reaches the model as exactly this:

```
Invalid JSON input for tool add.
```

One sentence. Not which argument, not what type it wanted, not what you sent. It is not an oversight: the SDK ships with `OPENAI_AGENTS_DONT_LOG_TOOL_DATA` defaulting to **on**, because tool arguments routinely contain personal data — amounts, emails, addresses — and echoing them into logs and traces by default would be a privacy incident waiting to happen.

**The SDK chose privacy over recoverability, and it chose on your behalf.**

`failure_error_function=` hands the decision back, per tool. Which means you can be verbose for `add` and silent for `charge_credit_card`.

> That is the real lesson of this chapter's SDK layer, and it generalises past this one flag: **a framework's defaults encode somebody else's judgement about your tradeoffs.** Knowing the mechanism underneath is what lets you notice when you disagree. That is why we build first.

The full line-by-line map is in [`with_sdk/compare.md`](with_sdk/compare.md).

### ▶ Practice 10 — read the two schemas side by side (10 min)

```powershell
uv run python 02_typed_tools/with_sdk/agent_sdk.py
```

The first thing it prints is the SDK's generated schema for `convert_temperature`. Put it next to yours:

```powershell
cd 02_typed_tools/from_scratch
uv run python -c "import json; from tools import convert_temperature as c; print(json.dumps(c.schema['function']['parameters'], indent=2))"
```

1. Name every difference.
2. One of them is `"title"` keys, which we strip and the SDK keeps. Who is right?
3. What is `strict_json_schema=True`, and why does it not make your validation redundant?

<details>
<summary>Spoiler for 3</summary>

`strict` asks the **provider** to constrain generation to the schema, so many invalid calls are never emitted at all. That is a layer you did not build and cannot build — it lives in the model server. It is also not universal: not every provider honours it, and Gemini's compatibility endpoint is not OpenAI. Defence at the door still has to exist.

</details>

### ▶ Practice 11 — override the default (15 min)

In `with_sdk/agent_sdk.py`, comment out `failure_error_function=explain_to_model` on `add`, and run the file. Compare the rejected-call output.

**You're done when:** you can state, in one sentence, what a model can do with each of the two messages.

---

## 11. Everything you just learned, in SDK vocabulary `[core]` · 15 min

Every idea from this chapter has a `@function_tool` spelling. This table is the one to keep:

| The idea | Ours | SDK |
|---|---|---|
| Closed set | `Literal[...]` | `Literal[...]` — **unchanged, it's Python** |
| Range / format | `Annotated[float, Field(gt=0)]` | **unchanged** |
| No invented arguments | `ConfigDict(extra="forbid")` | automatic — `additionalProperties: false` |
| Tool description | the docstring | the docstring |
| Argument descriptions | `Field(description=...)` | `Field(description=...)`, **or** an `Args:` block in the docstring |
| Rename the tool the model sees | *(we couldn't)* | `@function_tool(name_override="...")` |
| Error message policy | `explain()` | `failure_error_function=` |
| Hide a tool conditionally | *(we couldn't)* | `is_enabled=` |

The first four rows are the important ones: **your type annotations transfer to the SDK completely unchanged.** That is not a coincidence. Both designs read the same annotations because the annotations were always the right place to put the contract.

The last two rows are capabilities you did not build and now get for free. `is_enabled=` in particular is a trust primitive — a tool the model cannot see is a tool it cannot call — and it returns in the guardrails chapter.

### ▶ Practice 12 — the blank file (45 min) 🚀 **mandatory**

**This is the most important task in the chapter.** Everything before it had you read, predict or modify existing code. Recognising code and producing code are different skills, and only the second one is fluency.

Open a genuinely empty file: `exercises/dice_agent.py`. No copying from `with_sdk/`. Keep the docs open — that's what you'd do at work.

Build an SDK agent for a **dice and probability** assistant. Not expenses; the domain is deliberately unfamiliar so you can't pattern-match your way through it.

Three tools, all with `@function_tool`:

| Tool | Contract |
|---|---|
| `roll(sides, count)` | `sides` one of 4, 6, 8, 10, 12, 20 · `count` 1–100 · returns the individual rolls and the total |
| `probability_at_least(sides, count, target)` | all three positive ints, `target` reachable given `sides × count` · returns a percentage |
| `describe_dice(notation)` | a string like `"3d6"`, pattern-enforced · returns a plain-English reading |

Then run it against: *"Roll 3 six-sided dice, then tell me the chance of getting at least that total again."*

**You're done when:**

- [ ] the file imports from `agents`, and contains **no** hand-written JSON Schema
- [ ] `sides` is a `Literal`, not an `int` with an `if`
- [ ] `count` and `target` use `Annotated[int, Field(...)]` — no range checks in any function body
- [ ] `describe_dice("3z6")` is rejected **before** the body runs, and you can prove it (put a `print` on line 1 of the body and watch it not fire)
- [ ] one tool has a `failure_error_function` and you can say why that tool and not the others
- [ ] the agent answers the two-step question correctly in one run
- [ ] `uv run ruff check . ; uv run pyright` — clean

**If you get stuck for more than 15 minutes on a single error, that's the exercise working.** Write down what the error said and what you tried before you look anything up.

### ⚡ Challenge 12b — same agent, hostile user `[depth]` · 20 min

Ask your dice agent: *"Roll 3 dice with 7 sides."*

Seven-sided dice don't exist and your `Literal` says so. Record what the agent does. Then ask: *"Roll 1000 dice."*

**You're done when:** you can say which of the two failures the model recovered from gracefully, which it didn't, and what you'd change — a type, a message, or the prompt.

---

## ✅ Checkpoint 2 — the sentence

You should now be able to finish this without hedging:

> *"I saw the mechanism that turns a signature into a validated tool contract. The SDK does it with `@function_tool`. What it does for me is ______. What it decides for me that I should check is ______. And I have written one from an empty file."*

That last clause is not decoration. If you skipped Practice 12, you have not finished this chapter — you have read it.

---

## What this chapter cannot do

Name the limitation, because it is the hook for what comes next.

Your tools now reject bad **input**. Nothing yet checks the agent's **output** — the final message to the user is still free-form prose that no schema has ever seen. The model can be given perfect arguments, execute perfect tools, and still answer with a number it made up in the summary.

Input has a contract. Output does not. That is the next chapter.

### 🐞 And it is not hypothetical — it is happening in this chapter, right now

There is a **real defect in `solutions/expense_agent.py`, deliberately left in place.** It is marked with a comment block above `TASK`.

On some runs, the agent does everything right and still reports the wrong number:

```
-> log_expense(1500)                          <- logged
-> get_budget("Food & Dining")                <- 25000
-> month_total("Food & Dining")               <- 9000   (includes the 1500)
-> subtract(25000, 9000)                      <- 16000

FINAL ANSWER: "...you have 14,500 PKR remaining."
```

It subtracted the just-logged expense a second time. Every tool call is correct. The sentence is wrong.

**This chapter's dataset cannot see it.** The assertion is `"16000" in answer`, so on a bad run the failure is one anonymous line among thirty-four and reads as model noise. It went unnoticed for the entire chapter, and it was found only when Chapter 3 replaced that check with `reply.logged.remaining == 16000` — which named it on the first run.

### ▶ Practice 13 — see it for yourself (15 min) `[core]`

```powershell
uv run python 02_typed_tools/solutions/expense_agent.py
```

Run it **five times.** Each time, compare the number in the final sentence against what `subtract` actually returned in the trace above it.

1. How many of the five were wrong?
2. Would this chapter's golden dataset have failed on the wrong ones? Check the assertion in `check_expenses.py` `case_1` and answer precisely.
3. The prompt's last line is *"Finish with one clear sentence for the user, including the numbers you looked up."* Rewrite that line so the failure becomes impossible. Test your version five times.

**You're done when:** you have a wrong run recorded, and a rewritten prompt line that survives five runs.

> Compare your rewrite against the `REPORTING NUMBERS` block in `03_structured_outputs/solutions/expense_agent_v3.py` — that is the fix that shipped, and yours may well be better.
>
> Then sit with the uncomfortable part: **the fix is a prompt, not a type.** The reply was a positive float in a well-formed sentence. Nothing about its *shape* was wrong, so no schema could have objected and no validator could have caught it. Types stop bad values; schemas stop malformed answers; only a check that compares what was *said* against what was *computed* stops this one. Chapter 3 §8 is that argument in full.

---

## Where to go now

| Order | File | Track | What it is |
|---|---|---|---|
| 1 | [`EXERCISES.md`](EXERCISES.md) | 1️⃣ Drills | Warm-ups and guided builds — rotating domains, never expenses |
| 2 | [`PROJECT.md`](PROJECT.md) | 2️⃣ + 3️⃣ | **Spendly Lite v2** (the spine) **and** your own agent's v2 |
| 3 | [`../SDK_BRIDGE.md`](../SDK_BRIDGE.md) | — | The running map of our code → SDK abstraction |
| — | `exercises/` | — | **Your** workspace. Already wired into the quality gate |
| — | `solutions/` | — | Reference builds. **Open after you attempt, not before.** |
