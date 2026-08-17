# Chapter 2 — Exercises

> **Track 1️⃣ — Drills.** Small, isolated, disposable reps. Deliberately *not* expenses: the spine's job is expenses, and doing forty tasks in one domain teaches you that domain rather than the concept.
>
> | | Time | What |
> |---|---|---|
> | **Core** | **2 hrs** | Warm-ups 1–4 and Guided Build A |
> | **Full** | **6–8 hrs** | Core + Guided Builds B and C + both challenges |
>
> Work them in order. Each tier assumes the one before it.
>
> **The gate for every exercise, no exceptions:**
>
> ```powershell
> uv run ruff format .
> uv run ruff check .
> uv run pyright
> uv run pytest
> ```
>
> An exercise with a failing gate is not finished, however well it runs.

---

# Tier 1 — Warm-ups

*Can you read and edit this code?*

---

## Warm-up 1 — Add a typed tool `[core]` (15 min)

Add a tool to `from_scratch/tools.py`:

```python
@tool
def split_bill(total: ..., people: ..., tip_percent: ... = 0) -> float:
    """..."""
```

Requirements:

- `total` must be greater than zero
- `people` must be a whole number between 1 and 50
- `tip_percent` is optional, 0 to 100
- returns the amount each person owes, tip included, rounded to 2 decimals

Do **not** write a single `if` statement for any of those rules.

**You're done when:**

- [ ] `split_bill.schema` shows `exclusiveMinimum`, `minimum`/`maximum`, and the right `type` for each argument
- [ ] `split_bill.call('{"total": 3000, "people": 4, "tip_percent": 10}')` returns `825.0`
- [ ] `split_bill.call('{"total": 3000, "people": 0}')` raises `ToolError` naming `people`
- [ ] `split_bill.call('{"total": 3000, "people": 4.5}')` is rejected — and you can say why `4.5` is a *different* kind of wrong from `0`
- [ ] the agent uses it: add it to `ALL_TOOLS` and ask *"split a 3000 bill between 4 people with a 10% tip"*

---

## Warm-up 2 — Close a set that is currently open `[core]` (15 min)

`from_scratch/tools.py` has `percentage_of(value, percent)`. Suppose the product decides percentages are only ever used for three things: `"tax"`, `"discount"`, `"tip"`.

Add a required `purpose` argument that can only be one of those three, and make the returned string say which one it was.

**You're done when:**

- [ ] `"enum"` with exactly three values appears in the schema
- [ ] `percentage_of.call('{"value": 100, "percent": 5, "purpose": "vat"}')` is rejected, and the rejection **lists the three valid values**
- [ ] you can point at the exact line in `typed_tool.py` that put the enum in the schema

---

## Warm-up 3 — Break the schema, watch the model suffer `[core]` (20 min)

This one is about the contract, not the code. It touches the spine rather than a throwaway domain, because the point is what a broken contract does to *stored data* — and only the spine has stored data.

In `solutions/expense_tools.py`, change `category: Category` to `category: str` — nothing else. Run the golden dataset case 3 only:

```powershell
uv run python -c "
import sys; sys.path.insert(0, '02_typed_tools/solutions')
from check_expenses import CASES, run_from_scratch
import expense_store; expense_store.reset(seeded=True)
run = run_from_scratch(CASES[2].prompt)
print(run.final_answer)
print(run.executed_names)
print([r['category'] for r in expense_store.all_expenses() if r['notes'] != 'seed'])
"
```

**You're done when:**

- [ ] you have the output of the broken version saved somewhere
- [ ] you can state what got written to the ledger and why the agent believed it succeeded
- [ ] you restored `Category` and confirmed the case passes again
- [ ] you can answer: the tool's *behaviour* did not change at all — so what did?

---

## Warm-up 4 — The same tool, both ways `[core]` (20 min) 🚀

Take `split_bill` from Warm-up 1 and write it a second time in `exercises/split_sdk.py` — same constraints, same behaviour, but with `@function_tool` instead of `@tool`.

Change nothing about the annotations. That is the exercise: find out how little there is to change.

**You're done when:**

- [ ] the two function bodies are **identical**
- [ ] the two signatures are **identical**
- [ ] you can list every line that differs between the files — there should be very few
- [ ] you have printed both generated schemas and named every difference
- [ ] you can answer: if the annotations transfer unchanged, what exactly did you learn by writing `@tool` first?

> That last question is not rhetorical and it doesn't have a flattering answer in every case. Write down what you actually think.

---

# Tier 2 — Guided builds

*Can you apply the concepts to something new?*

> **Do Guided Build A.** B and C are `[depth]` — worthwhile, but not on the path to Chapter 3.

---

## Guided build A — A tool suite in an unfamiliar domain `[core]` (60 min) 🚀

Blank file: `exercises/library_agent.py`. SDK only — `@function_tool` throughout. No `@tool`, no hand-written schema.

You are building the tool layer for a **library catalogue** assistant. Four tools:

| Tool | Contract |
|---|---|
| `search_books(query, genre, max_results)` | `genre` a closed set of 8 · `max_results` 1–20, default 5 |
| `check_availability(isbn)` | `isbn` pattern-enforced: 13 digits, optional hyphens |
| `reserve(isbn, member_id, days)` | `days` one of 7, 14, 21 · `member_id` pattern `M` + 6 digits |
| `list_genres()` | no arguments — and getting "no arguments" right is its own small lesson |

Back them with an in-memory dict of ~10 books. The data is not the point; the contracts are.

**You're done when:**

- [ ] every constraint above is a type or a `Field` — **zero `if` statements** for validation
- [ ] `reserve` has a `failure_error_function` and the other three do not, and you can justify the split
- [ ] you wrote `test_library_tools.py` with **8 attack payloads**, no API key, under 2 seconds
- [ ] the agent handles *"find me a mystery novel and reserve it for two weeks"* — which requires chaining two tools
- [ ] the agent handles *"reserve ISBN 12345"* by **asking** for what's missing rather than inventing a member ID
- [ ] `uv run pyright` — 0 errors

> That second-to-last box is the one that fails most often, and it is a §7b problem, not a typing problem. If your agent invents a member ID, the fix is in the instructions, not the annotations.

---

## Guided build B — Your own `@tool` decorator, from an empty file `[depth]` (60–90 min)

> ### ⚠️ Read this before starting
>
> **This exercise is optional, and it used to be mandatory.** It was the largest single time investment in the chapter, and cutting it is a deliberate decision: it teaches Python metaprogramming, which is a fine thing to know and is not what this curriculum is for. `@function_tool` does this job in production and you will never ship your own.
>
> Do it if you want to understand `inspect` and `create_model` properly, or if you like this kind of puzzle. **Do not do it because you think Chapter 3 needs it.** It doesn't.

Do not copy `typed_tool.py`. Open a blank file, `my_tool.py`, and rebuild it. You may look at the finished version **only after** your version passes the acceptance tests below, or after 45 minutes of being genuinely stuck.

Build in this order — each step is testable on its own:

1. **Read the signature.** `inspect.signature()` + `get_type_hints(fn, include_extras=True)`. Print the parameter names, annotations and defaults for `def add(a: float, b: float = 1) -> float`.
2. **Build the field map.** `{name: (annotation, default_or_ellipsis)}`. Required parameters get `...`.
3. **Build the validator.** `pydantic.create_model(name, __config__=ConfigDict(extra="forbid"), **fields)`.
4. **Generate the schema.** `model_json_schema()`, wrapped in the `{"type": "function", "function": {...}}` envelope.
5. **Write `call()`.** parse → validate → dispatch → serialise, in that order.
6. **Write the error formatter.** Turn `ValidationError.errors()` into a message a model can act on.

### Acceptance tests

Put these in `test_my_tool.py`. All must pass:

```python
@tool
def greet(name: str, times: int = 1, style: Literal["formal", "casual"] = "casual") -> str:
    """Greet someone."""
    return " ".join([f"Hello {name}" if style == "formal" else f"hi {name}"] * times)
```

- [ ] `greet.schema["function"]["name"] == "greet"`
- [ ] the description is the docstring
- [ ] `required == ["name"]` — `times` and `style` have defaults, so they are not required
- [ ] `style` appears as an `enum` with two values
- [ ] `additionalProperties is False`
- [ ] `greet.call('{"name": "Faraz"}')` returns `"hi Faraz"`
- [ ] `greet.call('{"name": "Faraz", "times": "3"}')` **succeeds** — `"3"` coerces to `3`
- [ ] `greet.call('{"name": "Faraz", "style": "shouty"}')` raises, and the message contains `formal` and `casual`
- [ ] `greet.call('{"name": "Faraz", "extra": 1}')` raises, and the message contains `extra`
- [ ] `greet.call('{"name":')` raises, and the message says the JSON was invalid
- [ ] a tool with **no docstring** raises at decoration time, not at call time

### The question to answer when you are done

Step 6 was the longest step, and it produces no functionality — the validation already worked without it. Why is it not optional?

---

## Guided build C — Port Chapter 1's unit-converter agent `[depth]` (45 min)

`01_agent_loop/solutions/unit_tools.py` has a hand-written unit converter: hand-rolled schemas, string unit names, prose descriptions.

Rebuild it as `02_typed_tools/exercises/unit_tools.py` using `@tool`, and make every unit a `Literal`.

**You're done when:**

- [ ] the file has **zero** hand-written JSON Schema
- [ ] every unit argument is a closed set
- [ ] `uv run pytest` includes at least 8 attack cases you wrote for it
- [ ] you have measured it and can fill this in:

  | | Chapter 1 | Chapter 2 |
  |---|---|---|
  | lines in the tools file | | |
  | lines of schema | | |
  | invalid unit names reaching a function body | | |

- [ ] the agent answers *"convert 100 kilometres to miles, then tell me what 20% of that is"* correctly

---

# Tier 3 — Challenges `[depth]`

*No step-by-step. Design it yourself.*

---

## Challenge 1 — The adversarial dataset `[depth]` (90 min)

Write `exercises/test_adversarial.py`: **25 hostile payloads** against Spendly Lite v2's tools that are not already in `solutions/test_expense_tools.py`.

Rules:

- No API calls. The whole file must run in under 5 seconds.
- Every case must be something a **real model could plausibly emit** — not random fuzz. If you cannot write one sentence explaining what the model was thinking, the case does not count.
- Group them and say what property each group tests.
- At least **three** of your 25 must find a genuine gap. When they do: fix `expense_tools.py`, and leave the test.

Starting points for the kinds of thinking that produce good cases:

- What does a model send when the user says *"yeah log it"* and it has no amount?
- What does it send for *"I spent about two and a half thousand"*?
- What happens with a vendor name containing a newline? A `{`? 10,000 characters?
- What if the model sends the arguments **twice** — `{"amount": 1500, "amount": 2000}`?
- What if `expense_date` is `"2026-02-30"`? That matches the pattern.
- What if the user is in a different timezone from the server?

**You're done when:**

- [ ] 25 cases, grouped, each with a one-line rationale
- [ ] at least 3 found a real gap, and the gap is fixed
- [ ] `uv run pytest` is green
- [ ] you can name the **class** of attack you are still not defended against

> This file is the seed of your Chapter 6 golden dataset. Write it as though someone else will inherit it, because you will.

---

## Challenge 2 — Where does validation stop? `[depth]` (90 min)

Build one tool, `transfer_budget(from_category, to_category, amount)`, that moves money between two category budgets for the current month.

The rules:

1. both categories must be valid — *(type)*
2. they must be different — *(?)*
3. `amount` must be positive — *(type)*
4. `amount` must not exceed the unspent balance in `from_category` — *(?)*
5. transfers are not allowed after the 25th of the month — *(?)*

Implement all five, then write up — in a comment at the top of the file — which of the five could live in the type system, which could not, and **the general rule that separates them.**

Then answer the harder question:

> Rule 2 is a relationship between two arguments, not a property of either. Pydantic *can* express it, with a model-level validator. Should it be there, or in the function body? Argue it, then defend your choice against the strongest counter-argument you can construct.

**You're done when:**

- [ ] all five rules are enforced and tested
- [ ] `transfer_budget` has tests for both success and each failure mode
- [ ] your write-up states the general rule in one sentence
- [ ] you have argued rule 2 both ways and committed to one

<details>
<summary>A hint about the general rule, if you are stuck for 30 minutes</summary>

Ask of each rule: **to check this, do I need to look at anything other than the arguments themselves?**

</details>

---

## Where next

`PROJECT.md` — two tracks. **Spendly Lite v2** (the spine) combines every concept in this chapter into one thing you build twice and grade once. **Your Own Agent v2** applies the same concepts to the domain you picked in Chapter 1, from a blank file, graded on evidence.
