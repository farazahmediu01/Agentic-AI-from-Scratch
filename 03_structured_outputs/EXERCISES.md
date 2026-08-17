# Chapter 3 — Exercises

> **Track 1️⃣ — Drills.** Small, isolated, disposable reps in **rotating throwaway domains** — weather and recipes here. Never expenses; that is the spine's job.
>
> | | Time | What |
> |---|---|---|
> | **Core** | **1.5 hrs** | Warm-ups 1–3 and Guided Build A |
> | **Full** | **4 hrs** | Core + Guided Build B + both challenges |
>
> Every drill in this chapter is **SDK-native**. From Chapter 3 on, at least half of Track 1 is written directly against the Agents SDK with no hand-rolled layer, because a student who has only ever *modified* SDK code cannot write it.
>
> **The gate for every exercise, no exceptions:**
>
> ```powershell
> uv run ruff format . ; uv run ruff check . ; uv run pyright ; uv run pytest
> ```

---

# Tier 1 — Warm-ups

*Can you read and edit an output contract?*

---

## Warm-up 1 — Add a field that cannot be invented `[core]` (20 min) 🚀

Create `exercises/weather_agent.py`. One tool, `get_forecast(city, days)`, returning canned data for four cities. Output model:

```python
class Forecast(BaseModel):
    summary: str
    high_c: float
    low_c: float
```

Now add `chance_of_rain_percent`. The catch: your canned data has rain figures for **two** of the four cities and not the others.

**You're done when:**

- [ ] asking about a city *with* rain data returns a number
- [ ] asking about a city *without* rain data does **not** return an invented number
- [ ] you did it with the type, not with a sentence in the prompt
- [ ] you can state the general rule in one line

> If your fix was `Field(description="leave blank if unknown")`, you asked. Go back and make it structural.

---

## Warm-up 2 — Close a set that is currently open `[core]` (15 min) 🚀

Add `alert: str` to `Forecast` — values like `"heat warning"`, `"flood watch"`, `"none"`.

Run it five times against the same city and collect the strings you get back. Then convert `alert` to a `Literal` over the exact set you decided on, and run five more times.

**You're done when:**

- [ ] you have the five free-text values written down, and at least two are phrasings of the same thing
- [ ] the `Literal` version returns one of your values every time
- [ ] you can say what an eval asserting on the free-text version would have had to do

---

## Warm-up 3 — Convert an eval `[core]` (25 min)

Open `01_agent_loop/solutions/check_expenses.py` (or your own Chapter 1 build). Every assertion in it is a substring check.

Pick **three**. For each, write down: the current check, one wrong answer that would pass it, and the field assertion that replaces it once the agent has an `output_type`.

**You're done when:** you have three rows, each with a concrete false positive. You do not need to run anything — this is a reading exercise, and it is the one that makes §9 land.

---

# Tier 2 — Guided builds

> **Do Guided Build A.** B is `[depth]`.

---

## Guided build A — A union output in an unfamiliar domain `[core]` (60 min) 🚀

Blank file: `exercises/recipe_agent.py`. SDK only.

A recipe assistant with one tool, `pantry()`, returning a fixed list of ~12 ingredients. The user asks for something to cook. Three outcomes:

| Branch | Fields |
|---|---|
| `CanCook` | `recipe_name`, `steps: list[str]`, `uses: list[str]` (ingredients from the pantry) |
| `MissingIngredients` | `recipe_name`, `missing: list[str]`, `substitutions: list[str] \| None` |
| `NeedMoreInfo` | `question`, `missing: list[Literal["meal_type", "servings", "dietary"]]` |

**You're done when:**

- [ ] a `model_validator` enforces exactly one branch, and you have a test proving `{}` is rejected
- [ ] *"make me something with chicken"* when the pantry has no chicken returns `MissingIngredients`, **not** a hallucinated recipe
- [ ] *"I'm hungry"* returns `NeedMoreInfo`
- [ ] `uses` only ever contains ingredients the tool actually returned — and you have a check that verifies it, not a prompt that requests it
- [ ] `test_recipe_replies.py` has 6 offline tests, no API key, under 2 seconds
- [ ] `uv run pyright` — 0 errors

> The `uses` check is the important box. It is a §8 cross-check: the agent can produce a perfectly-shaped `CanCook` listing an ingredient nobody has. Shape is not truth, and you now write the code that knows the difference.

---

## Guided build B — Build the thing the SDK saved you from `[depth]` (60 min)

Write the retry-and-repair loop `output_type=` replaces: call the model, `tolerant_parse`, validate, and on failure send the **validation errors back** and try again, up to 3 times.

Use `from_scratch/prompt_and_parse.py` as the starting point. Measure across 20 runs: how many succeed first try, how many need a repair round, how many exhaust the budget, and the total call count versus 20.

**You're done when:**

- [ ] the loop works and you have the four numbers
- [ ] you can state the extra cost as a percentage
- [ ] you can name the failure mode a repair loop **cannot** fix
- [ ] you have an opinion on whether the repair message should include the raw invalid output

> Optional, and honest about why: this is a real technique for providers with no structured-output support, and it is genuinely useful to have written once. It is not on the path to Chapter 4.

---

# Tier 3 — Challenges `[depth]`

*No step-by-step. Design it yourself.*

---

## Challenge 1 — The fabrication audit `[depth]` (90 min)

Take any output model in this chapter — yours or `replies.py` — and audit every field with one question: **what does the model put here when it genuinely does not know?**

Then prove it. For each field, construct a prompt where that value is genuinely unavailable, run it 5 times, and record what came back.

**You're done when:**

- [ ] every field has 5 recorded runs under genuine ignorance
- [ ] you have ranked the fields by how often they were fabricated
- [ ] the worst offender is fixed structurally, and the fix is re-tested
- [ ] you can state which *kinds* of field attract invention

> The pattern generalises hard. Numbers get invented more than strings; scores more than counts; anything phrased as a confidence more than anything phrased as a fact.

---

## Challenge 2 — Where does the enum stop? `[depth]` (60 min)

`Refused.reason` is `Literal["negative_amount", "future_date", "unknown_category", "other"]`.

Case 9 in the golden dataset sends `Log 0 at Metro` — and zero is not negative. The model must map it onto `negative_amount`, which is a lie about the taxonomy, or `other`, which discards the information.

Argue it out and commit to a design:

1. Add `zero_amount`. What happens the next time a new refusal reason appears?
2. Drop the enum for free text. What breaks in `check_expenses.py`?
3. Keep `other` but add `detail: str`. What is that actually costing you?

**You're done when:**

- [ ] you have implemented one of the three
- [ ] `check_expenses.py` case 9 is updated to match, and passes
- [ ] you have written the general rule for **when a closed set should be closed** in one sentence
- [ ] you can name what `other` is for, and what it must never become

---

## Where next

`PROJECT.md` — **Spendly Lite v3** (the spine, now SDK-only) and **Your Own Agent v3**.
