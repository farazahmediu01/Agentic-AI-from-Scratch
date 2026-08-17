# Chapter 3 — Structured Outputs

> **Axes:** 📐 **Proof** (primary) · 🧠 State (secondary)
>
> **You built:** an agent whose tools cannot be called wrongly.
> **You will build:** an agent whose *answers* have a shape — and evals that stop guessing.

| Part | Core | Full |
|---|---|---|
| This README (§1–§10) | 5 hrs | 6.5 hrs |
| [`EXERCISES.md`](EXERCISES.md) — Track 1️⃣ drills | 1.5 hrs | 4 hrs |
| [`PROJECT.md`](PROJECT.md) — Tracks 2️⃣ + 3️⃣ | 3 hrs | 4.5 hrs |
| **Chapter total** | **≈ 9.5 hrs** | **≈ 15 hrs** |

**Plan 2–3 sessions.** Every section is marked `[core]` or `[depth]` and carries its own estimate; the totals above are their sum.

> ### 🔨 This chapter hand-rolls almost nothing, and that is the design
>
> Chapters 1 and 2 built mechanisms by hand because you must be able to picture them while debugging. This chapter's hand-rolled layer is **one ~60-line spike that fails on purpose** — you write it, watch it break in five different ways, and throw it away.
>
> That is not a shortcut. It is the honest shape of this particular mechanism: prompt-and-parse is not a simplified version of `output_type=`, it is a *different and worse* approach, and the fastest way to understand why the SDK does what it does is to spend thirty minutes failing to do it yourself. From §4 on, everything is the SDK.

---

## Before you start

You need Chapter 2 finished. This chapter **imports** Chapter 2's storage and tools rather than copying them — from here the spine is one continuous codebase, not a fresh copy per chapter.

```powershell
uv sync
uv run python 02_typed_tools/solutions/expense_agent.py   # should still work
uv run pytest                                             # should be green
```

---

## 1. The failure this chapter fixes `[core]` · 20 min

Chapter 2 ended with an agent that cannot be called wrongly. Here is a **real run of it**, captured while writing this chapter. Every single tool call is correct:

```
-> log_expense({"vendor":"KFC","amount":1500,"category":"Food & Dining"})   <- logged
-> get_budget({"category":"Food & Dining"})                                 <- 25000
-> month_total({"category":"Food & Dining"})                                <- 9000
-> subtract({"a":25000,"b":9000})                                           <- 16000

FINAL ANSWER: "I have logged your 1,500 PKR lunch at KFC, and you have
               14,500 PKR remaining in your Food & Dining budget."
```

Read the last line against the tool results. `subtract` returned **16000**. The sentence says **14,500**.

The model took `month_total`'s 9000 — which *already includes* the 1500 it had just logged — and then subtracted that 1500 a second time. Every argument was validated. Every tool executed. The ledger is perfect. And the user was told a number no tool ever produced, in a confident, well-formed sentence.

> **This was not written for the chapter. It was found by the chapter**, on the first run of the new golden dataset, and it had been happening in Chapter 2 the whole time. The old assertion was `"16000" in answer`; when the answer said 14,500 that check failed *silently among 34 others* and got attributed to model noise. The typed assertion `reply.logged.remaining == 16000` named it in one line.
>
> Keep that in view for the rest of the chapter: **the reason to make an output typed is not tidiness. It is that you cannot fix a class of bug you cannot see.**
>
> The fix, when it came, was not a type. It was four lines in the system prompt telling the model to report exactly what `subtract` returned and never to adjust it — the Chapter 1 rule about arithmetic, which had quietly stopped being enforced. Read `expense_agent_v3.py`'s `REPORTING NUMBERS` section.

> ### 🧠 Mental model: you validated the kitchen and forgot the waiter
>
> Chapter 2's boundary sits between the model and your functions. Nothing gets *in* without a contract.
>
> But there is a second boundary, on the way out, between your agent and the user — and it has nothing on it at all. The final message is free-form prose. No schema has ever seen it. The model can execute a flawless sequence of tools and then summarise them incorrectly, and **there is no layer in your system whose job is to notice.**
>
> Chapter 2 asked *"what happens when the model calls my function wrongly?"* This chapter asks *"what happens when the model reports its own work wrongly?"*

### ▶ Practice 1 — find the seam yourself (15 min)

Open `02_typed_tools/solutions/check_expenses.py` and read `case_1`. Find this line:

```python
(f"the answer states {remaining:.0f} remaining", str(int(remaining)) in answer),
```

1. Write down **two different final answers** that would pass this check while being wrong. (Hint: one where the number appears in the wrong role; one where the number appears inside a larger number.)
2. Now find `case_4`'s check that the agent "asks for the amount or the vendor". Write one reply that passes it without asking anything.
3. In one sentence: what is that check actually testing?

**You're done when:** you have three written examples and can state what the eval is really measuring. Keep them — §9 comes back to this.

<details>
<summary>Spoiler, once you have tried</summary>

It is testing **the presence of a substring in prose**, which is a proxy for the thing you care about, not the thing itself. `"16000" in answer` passes on *"you have spent 16000 of your 16000 budget"*. `"amount" in answer` passes on *"I logged that amount for you."*

Every eval in the curriculum so far has been a classifier built out of `str.find`. It has been quietly wrong in both directions the whole time.

</details>

---

## 2. The naive fix — ask for JSON `[core]` 🔨 · 30 min

The obvious move: tell the model to reply with JSON, then parse it.

```powershell
uv run python 03_structured_outputs/from_scratch/prompt_and_parse.py
```

No API key needed. It replays **eight real Gemini responses** to a prompt that asks for JSON about as explicitly as anyone reasonably could — *"Reply with a single JSON object and NOTHING else. No prose, no markdown, no code fences."*

```
specimen                   json.loads              tolerant                validated
clean                      ok                      ok                      ok
fenced                     FAIL Expecting valu...  ok                      ok
preamble                   FAIL Expecting valu...  ok                      ok
trailing comma             FAIL Expecting prop...  ok                      ok
numbers as strings         ok                      ok                      ok
invented key, missing key  ok                      ok                      FAIL remaining: Field required
single quotes              FAIL Expecting prop...  FAIL Expecting prop...  -
apologised mid-object      FAIL Extra data: li...  ok                      ok

  parsed by json.loads      : 3/8
  parsed by tolerant_parse  : 7/8
  survived validation       : 6/8
```

**Three out of eight.** The prompt said "no code fences" and the model used code fences. It said "nothing else" and the model added *"Let me know if you'd like this in a different format!"*

The file then does what everyone does next: a `tolerant_parse` that strips fences, regex-finds the outermost `{...}`, and deletes trailing commas. That climbs to 7/8.

Read those two functions and notice the shape of the second one. Every line in it was added in response to one specific failure. **That is exactly how this function grows in a real codebase — one incident at a time, until nobody remembers which line defends against what.**

### ▶ Practice 2 — extend the tolerant parser (20 min)

Specimen 7 (single quotes) still fails. Make it pass.

Then answer, in a comment above your fix:

1. What did your change break? (Try it against a `reply` field whose text legitimately contains an apostrophe — `"reply": "It's logged."`)
2. How many specimens would you need before you would rather write a real parser than another regex?

**You're done when:** single quotes parse, you have found at least one input your fix breaks, and you have written the number down.

### ▶ Practice 3 — see it live (10 min)

```powershell
uv run python 03_structured_outputs/from_scratch/prompt_and_parse.py --live 6
```

Six real calls. **You will get a different distribution of failures than the captured set.** That is the point, and it is worth sitting with for a moment: you cannot enumerate the failure modes of a sampler by observing it.

**You're done when:** you have one live failure mode that is not in the eight specimens.

---

## 3. Why prompting cannot close this `[core]` · 25 min

Look at the two numbers again: **7/8 parsed, 6/8 validated.**

The tolerant parser bought back every response that was merely *wrapped* wrong — fences, preamble, a trailing apology. It bought back **none** of the responses that were *shaped* wrong, and no amount of regex ever will, because a missing `remaining` key is not a punctuation problem.

Now the deeper issue. Suppose you got to 8/8. You still have nothing, because:

| What you have | What you need |
|---|---|
| It worked on these 8 | It works on the next 10,000 |
| A prompt that *asks* for a shape | A contract that *constrains* the shape |
| Sampling behaviour you observed | A guarantee you can rely on |

A system prompt is a **request**, evaluated by a probabilistic sampler. Chapter 2 taught this exact lesson about the *input* side — §5 there compared a category "requested" in a description against a category enforced by a `Literal`. This is the same distinction, pointed the other way.

> ### 🔒 The escalation ladder, which you have now climbed twice
>
> | Level | Mechanism | Guarantee |
> |---|---|---|
> | Prose | "please reply with JSON" | none |
> | Parsing | `json.loads` + regex | recovers *format* errors, never *shape* errors |
> | Validation after the fact | `Model.model_validate(parsed)` | detects a bad shape — after you already paid for it |
> | **Constrained generation** | `output_type=` | the provider is told the schema and constrained to it |
>
> Every rung moves enforcement further from persuasion and closer to code. You saw the same ladder in Chapter 2 §7b: **prose → type → boundary → guardrail.**

### ▶ Practice 4 — cost the retry loop (15 min)

`tolerant_parse` raising means you must call the model again. Sketch that retry loop — you do not have to run it — and answer:

1. How many extra API calls does a 6/8 success rate cost you per 100 user messages?
2. What do you send back on retry? (If your answer is "the same prompt", why would the second attempt do better?)
3. What is your ceiling, and what happens to the user when you hit it?

**You're done when:** you have a number for (1) and an honest answer for (2). Most people's honest answer to (2) is *"nothing useful"*, which is the correct answer and the reason this approach loses.

---

## ✅ Checkpoint 1

Before the SDK layer:

1. Why did `tolerant_parse` fix "fenced" but not "invented key, missing key"?
2. `numbers as strings` passed validation. Why — and which Chapter 2 concept explains it?
3. State the difference between a prompt that asks for a shape and a type that constrains one.

<details>
<summary>Answer to 2, since it catches people</summary>

Pydantic's default lax mode coerces `"1500"` into `1500.0`. This is the same lax-mode behaviour that let `amount: true` become `1.0` in Chapter 2 §6 — the trap that needed a `BeforeValidator`.

It is worth noticing that lax coercion is *helping* here and *hurting* there. A default is not good or bad on its own; it is good or bad for a purpose. Knowing the mechanism is what lets you tell which.

</details>

---

## 4. `output_type=` — the contract on the way out `[core]` 🚀 · 30 min

Everything above, in one argument:

```python
agent = Agent(name="Spendly", instructions=..., model=..., output_type=ExpenseReply)

result = await Runner.run(agent, "I spent 1500 at KFC on lunch.")
result.final_output.amount      # 1500.0  — a float, not a string that looks like one
```

`result.final_output` is an `ExpenseReply` **instance**. Not a string you hope is JSON. Not a dict you have to check. The typed object, or an exception.

```powershell
uv run python 03_structured_outputs/with_sdk/agent_sdk.py
```

The first thing it prints is the JSON Schema generated from the Pydantic model — and you have seen this before. It is the same three moves as Chapter 2's `@tool`: **read the annotations, build a validator, publish the schema.** Pointed at the output instead of the input.

> ### 🧠 Mental model: the same machine, turned around
>
> | | Chapter 2 (input) | Chapter 3 (output) |
> |---|---|---|
> | Declared by | a function signature | a Pydantic model |
> | Published as | the tool's `parameters` schema | the response format schema |
> | Enforced | before your function body runs | before `final_output` reaches you |
> | On violation | `ToolError` the model can read | `ModelBehaviorError` |
>
> There is genuinely only one idea in this repository's middle chapters: **put the contract where the untrusted thing crosses your boundary, and generate it from a declaration you were writing anyway.** Chapter 2 did the inbound crossing. Chapter 3 does the outbound one.

### ▶ Practice 5 — make it fail (15 min)

In `with_sdk/agent_sdk.py`, change `ExpenseReply.amount` to:

```python
amount: float = Field(gt=1_000_000, description="The amount that was logged, in PKR.")
```

Run it and read the error carefully.

1. What exception type comes back, and at what point in the run?
2. Did the tool calls still happen?
3. Restore it. Then remove the `description=` from `category` and re-run — does behaviour change? Should it?

**You're done when:** you can say where in the run the output contract is enforced, and whether tool side effects survive a rejected output.

---

## 5. What the SDK actually sends `[depth]` · 25 min

*Skip on a first pass. Nothing later depends on it.*

`output_type=` compiles to a provider-level request. On Chat Completions the SDK sets:

```json
"response_format": {
  "type": "json_schema",
  "json_schema": { "name": "...", "strict": true, "schema": { ... } }
}
```

`strict: true` is the interesting part. It asks the **provider** to constrain generation — to make tokens that would violate the schema unavailable at sampling time. That is a guarantee you cannot build, because it lives in the model server, below any code you can write.

Three things worth knowing:

- **It is not universal.** Not every provider honours `strict`, and Gemini's compatibility endpoint is not OpenAI. The SDK validates the result regardless, which is why you still get an exception rather than a bad object.
- **Strict mode restricts the schema.** Many JSON Schema keywords are disallowed in strict mode. This is why a top-level `anyOf` (a bare `A | B` union) is less portable than one wrapper model with optional fields — see §7.
- **You still validate.** Constrained decoding reduces the failure rate; it does not remove the need for the check. Same argument as `strict_json_schema=True` for tools in Chapter 2 §10.

### ▶ Practice 5b — read the wire `[depth]` (15 min)

Print `ExpenseReply.model_json_schema()` and compare it to the tool schema `@function_tool` generated in Chapter 2 for `log_expense`.

**You're done when:** you can name every structural difference and say which are caused by *input vs output* and which by *strict mode*.

---

## 6. Designing the output model `[core]` · 30 min

The mechanism is one argument. The **design** is the chapter, and it is where students actually go wrong.

Open `solutions/replies.py`. Two rules are doing all the work:

**Rule 1 — a field that must be filled will be filled, truthfully or otherwise.**

```python
class Reported(BaseModel):
    spent: float | None = None      # optional ON PURPOSE
```

If `spent` were required, then "what categories exist?" — a question with no number in it — would force the model to produce a number. You will get one. It will be invented. **A required field is an instruction to always have an answer**, and there is no shape of "I don't have one" unless you build it.

**Rule 2 — an enum where you would otherwise grep.**

```python
reason: Literal["negative_amount", "future_date", "unknown_category", "other"]
```

If `reason` were a free-text string, your eval would be back to searching prose for the word "negative". The enum turns the model's own explanation into a value you can assert on, count, and group by.

### ▶ Practice 6 — find the fabrication pressure (20 min)

Here is a badly designed output model:

```python
class SearchResult(BaseModel):
    answer: str
    confidence: float = Field(ge=0, le=1)
    sources: list[str]
    page_number: int
```

Three of these four fields will produce invented data. For each one, write:

- what the model does when it genuinely does not have that value
- how you would fix the field

**You're done when:** you have identified at least three and your fixes use `| None`, a union branch, or a `Literal` — not a longer description.

<details>
<summary>The one people miss</summary>

`confidence: float`. Models do not have calibrated confidence; asking for a number between 0 and 1 produces `0.95` almost every time, because that is what confident-sounding text looks like in the training data. It reads like a measurement and is closer to a genre convention. If you need confidence, derive it from something you can observe — did a tool return results, did two sources agree — not from asking.

</details>

---

## 7. Unions — letting the agent say "I can't" `[core]` 🚀 · 65 min

This is the most valuable section in the chapter.

A **single rigid output model is how you teach an agent to fabricate.** If the only shape it may return requires an `amount`, it will produce an `amount` whether or not you gave it one. You did not ask it to lie; you removed every other shape it could take.

```python
class SpendlyReply(BaseModel):
    logged: Logged | None = None
    reported: Reported | None = None
    need_more_info: NeedMoreInfo | None = None
    refused: Refused | None = None
```

Four outcomes, one of which is *"I need to ask you something"* and one of which is *"I will not do that."*

Now look back at Chapter 2's golden dataset and re-read it as a list of **outcomes** rather than prompts. Cases 1 and 6 are `logged`. Case 2 is `reported`. Cases 3 and 4 are `need_more_info`. Cases 5 and 7 are `refused`.

**The dataset was already classifying every run into these four buckets.** It just had to do it by searching the final sentence for substrings. The union does not add a category system — it makes the one you already had explicit and checkable.

> ### 🔒 From requested behaviour to reachable shape
>
> Chapter 2 taught the agent to ask instead of guessing with a line in the system prompt. That was a **request**, and §7b showed it being ignored.
>
> A union makes "I need to ask" a **shape the model can reach**. Choosing it is now a normal outcome rather than a deviation from the only format you allowed. That is a real reduction in fabrication pressure, and it is why this is the section that matters.

### The two failures a union cannot prevent

`output_type=SpendlyReply` guarantees you get a `SpendlyReply`. It does not guarantee the object means anything — the model can set **zero** branches or **two**:

```python
@model_validator(mode="after")
def exactly_one_branch(self) -> SpendlyReply:
    ...
```

Read that validator in `replies.py` and notice **where it had to live**. Not in the type — JSON Schema cannot portably say "exactly one of these four is non-null". Not in the prompt — that is a request again. It runs on the result, after the model has spoken, and it cannot be talked out of its job.

That is a **guardrail**, and it is your first one. Chapter 8 gives them a name and a decorator.

### 🐞 The cost nobody mentions: a union makes refusing *cheap*

Everything above is the case for unions. Here is the bill, and it was found the expensive way — by this chapter breaking a case Chapter 2 had passed.

Chapter 2's dataset case 6 is a **recovery** case:

```
"Log 1200 at Careem for transportation on 05/08/2026 (the 5th of August)."
```

The date is unambiguous — the user says which date they mean — but written in a format the schema forbids. Chapter 2's agent got rejected once, read the error, converted it to `2026-08-05`, and logged it. That is the behaviour the whole of Chapter 2 §7 was written to produce.

Chapter 3's first version of this agent **refused it**, on turn one, without attempting the call:

```
branch=refused  turns=1        <- Chapter 2 passed this. Chapter 3 broke it.
```

Nothing about the tools changed. Nothing about the types changed. What changed is that **refusing became a well-typed, first-class, obviously-correct-looking thing to do** — and the model reached for it.

> ### 🧠 The symmetry worth carrying out of this chapter
>
> §7's argument is that a rigid single shape creates **fabrication pressure**: if the only output demands an `amount`, the model produces an `amount` it does not have.
>
> The mirror is just as real. A branch named `refused` creates **refusal pressure**: if there is a clean, valid, blameless way to decline, declining gets easier — and an agent that refuses work it could have done is broken in a quieter way than one that invents.
>
> **Every branch you add is a road you have paved.** Traffic will use it. That is the point, and it is also the cost.

The fix was not a type. It was making the *judgement* explicit in the prompt, because branch selection is judgement and always was:

```
REFORMATTING IS NOT CORRECTING. If the date is unambiguous but written in
another format, convert it and carry on. Refuse only when it is impossible,
in the future, or genuinely ambiguous.

`refused` is the LAST resort, not the safe default.
```

Read `expense_agent_v3.py`'s prompt for both blocks in full. Then notice what the regression rule bought you: **this was caught because Chapter 2's cases are still in Chapter 3's dataset.** A curriculum that started a fresh dataset each chapter would have shipped it.

### ▶ Practice 7c — feel the pressure yourself (20 min) `[core]`

Delete the two sentences above from `SYSTEM_PROMPT` — the `REFORMATTING IS NOT CORRECTING` block and the `last resort` line. Run case 6 three times:

```powershell
uv run python 03_structured_outputs/solutions/check_expenses.py --only 6
```

1. How many of the three refused a date they could have read?
2. Restore the block, run three more. Did it hold?
3. Now the design question: could you have prevented this with a **type** instead of a prompt? Try to write one. What would it have to know?

**You're done when:** you have both sets of three runs recorded, and a written answer to (3).

<details>
<summary>The answer to 3, which is the whole chapter in one paragraph</summary>

You cannot. "Is this date reformattable or genuinely unusable?" depends on what the user meant, which is not a property of the value's shape. A type can say `IsoDate` must match a pattern. It cannot say *"if they told you which day they meant, believe them."*

Shape is checkable. Judgement is not. Which is why §8 exists.

</details>

### ▶ Practice 7 — add a branch (25 min)

Spendly cannot currently express *"I did the thing you asked, but you should know something."* Add a fifth branch: `LoggedWithWarning` — the expense was recorded **and** the category is now over budget.

1. Add the model to `replies.py`.
2. Update `exactly_one_branch`.
3. Add the routing rule to the prompt in `expense_agent_v3.py`.
4. Run it with `"Log 20000 at Metro for groceries."`

**You're done when:** the new branch fires, `exactly_one_branch` still passes, and you can answer: **why did adding one outcome require touching a prompt as well as a type?**

### ⚡ Challenge 7b — the design smell `[depth]` · 20 min

Five branches is fine. Fifteen is not.

Argue this both ways in three sentences each, then commit: *at what point does an output union stop being a contract and become a state machine you should have built explicitly?*

---

## 8. A schema guarantees shape, not truth `[core]` · 25 min

**The most important section in the chapter.** It is the direct sequel to Chapter 2 §7b, and if you only remember one page from Chapter 3, this is it.

Open `solutions/test_replies.py` and find `test_a_valid_shape_can_still_be_a_lie`. It **passes**, and that is the point:

```python
reply = SpendlyReply.model_validate({
    "logged": {
        "reply": "Logged PKR 999999 at Definitely Real Vendor.",
        "vendor": "Definitely Real Vendor",
        "amount": 999999,
        "category": "Groceries",
        "remaining": 123456,
    }
})
```

Every constraint is satisfied. The amount is positive. The category is real. Exactly one branch is set. **And nothing was written to any ledger, no budget was consulted, and both numbers are invented.**

> | | stops | does not stop |
> |---|---|---|
> | **A type** (Ch2) | a bad value being **accepted** | the model **manufacturing** a good one |
> | **A schema** (Ch3) | a malformed **answer** | a well-formed **false** one |
> | **A guardrail** (Ch8) | *(this is what you need)* | |

Chapter 1's failure was arithmetic done in the model's head. Chapter 2's was a fabricated `450`. Chapter 3's is a well-typed `remaining` that does not match what the tools returned. **It is the same failure wearing better clothes each time**, and each chapter's new mechanism narrows it without closing it.

Where does the guarantee have to live? Outside the model — a check that compares `reply.logged.remaining` against what `subtract` actually returned. You now have both as *values*, which is the first time in this curriculum that comparison has been possible at all.

> ### The §1 bug, revisited — and why a prompt fixed it
>
> §1's real defect (`subtract` → 16000, sentence → 14,500) was fixed by four lines of prompt, not by a type. Notice why: the reply's **shape** was flawless. `remaining` was a positive float in a correctly-chosen `logged` branch. No schema could have objected, because nothing about it was malformed — it was simply *false*.
>
> So the chapter's own headline mechanism did not fix the chapter's own headline bug. What it did was **make the bug visible**, which is what allowed a prompt fix to be verified instead of hoped for.
>
> That is the honest relationship between the three layers, and it is worth stating plainly rather than letting students infer it:
>
> | Layer | Job |
> |---|---|
> | The **type** | make the failure impossible to express |
> | The **schema** | make the failure impossible to *hide* |
> | The **cross-check** | make the failure impossible to *ship* |
>
> A prompt is none of these. It reduces the rate. It is not a guarantee, and §7b of Chapter 2 is the proof — the same prompt fix was applied there and case 5 still failed on some runs.

### ▶ Practice 8 — build the cross-check (25 min)

Write `verify_reply(run) -> list[str]` returning a list of discrepancies. Compare the typed reply against the tool results in `run.tool_arguments` and the ledger:

- if `branch == "logged"`, does `reply.logged.amount` equal the amount actually passed to `log_expense`?
- does `reply.logged.remaining` equal `get_budget - month_total`?
- if `branch == "logged"`, is there actually a new row in the ledger?

**You're done when:** it returns `[]` on a good run, and you have produced one run where it returns a real discrepancy. (Ask for something requiring arithmetic across three tools; that is where summaries drift.)

> This function is the seed of Chapter 6's eval harness and Chapter 8's output guardrail. You are building it a chapter early because you can finally express it.

---

## 9. What it unlocks: evals stop guessing `[core]` · 30 min

Go back to your Practice 1 notes.

```python
# Chapter 2
("the answer states 17500 remaining", "17500" in answer)
("it asks for the amount", "how much" in answer or "amount" in answer)

# Chapter 3
("reply.logged.remaining == 17500", run.reply.logged.remaining == 17500)
("missing == ['category']", run.reply.need_more_info.missing == ["category"])
```

The second pair cannot be satisfied by an unlucky substring. Open `solutions/check_expenses.py` — Chapter 2's seven cases are all there, converted, plus two that could not be written before:

- **Case 8** — vendor and amount given, category missing. Asserts `missing == ["category"]` **exactly**. An agent that re-asks for an amount you already gave it is broken in a way no substring test can see.
- **Case 9** — `Log 0 at Metro`. Asserts on the refusal *reason*, not on prose.

> ### 📐 This is why structured outputs sit at Chapter 3
>
> Not because it is the next feature. Because **evals are unassertable without it**, and Chapter 6 automates evals.
>
> Chapter 2 made the input boundary a pure function and bought 46 unit tests. Chapter 3 makes the output a typed value and buys evals that mean something. Each chapter's real payoff is what it makes *testable*.

### ▶ Practice 9 — convert an assertion (20 min)

Pick any substring check in `02_typed_tools/solutions/check_expenses.py` that is **not** already converted in Chapter 3's version. Convert it, and write one sentence on what the old version could have been fooled by.

**You're done when:** the converted check passes on a real run and you have named the false positive it removes.

---

## 10. The blank file `[core]` 🚀 · 45 min — **mandatory**

Everything before this had you read or modify. This is where you produce.

Open `exercises/triage_agent.py`, empty. SDK only. Not expenses.

Build a **support-ticket triage agent**. One tool, `search_kb(query)`, returning canned articles from a dict of five. The output is a union of three branches:

| Branch | When |
|---|---|
| `Resolved` | the KB answered it — needs `article_id` and `answer` |
| `Escalate` | it needs a human — needs `severity: Literal["low","medium","high"]` and `reason` |
| `NeedMoreInfo` | the ticket is too vague — needs `question` and `missing: list[...]` |

**You're done when:**

- [ ] `output_type=` is set and `result.final_output` is your union model
- [ ] a `model_validator` enforces exactly one branch
- [ ] **no field forces invention** — every value the agent might not have is `| None` or lives in a branch
- [ ] every closed set is a `Literal`, not a `str`
- [ ] three runs, one hitting each branch, pasted into `RUNS.md`
- [ ] a fourth run where you deliberately give it a ticket that *should* escalate but the KB has a tempting near-match article — record which branch it chose
- [ ] `uv run ruff check . ; uv run pyright` — clean

> That fourth run is the real test. An agent that resolves a ticket it should have escalated is exactly the §8 failure: correct shape, wrong content.

---

## ✅ Checkpoint 2 — the sentence

> *"I saw why asking a model for JSON cannot be made reliable. `output_type=` does it with a schema the provider enforces. What it guarantees for me is ______. What it does **not** guarantee is ______, and the check for that has to live ______."*

If you skipped Practice 10, you have read this chapter rather than finished it.

---

## What this chapter cannot do

Your agent's input has a contract and its output has a contract. It still has **no memory.**

Every run starts from nothing. Ask it to log an expense and then say "actually make that 2000" and it has no idea what "that" refers to — the message list you built in Chapter 1 is thrown away between runs. Case 8's agent asks *"which category?"*, the user answers, and the agent has already forgotten the vendor and the amount it was asking about.

A typed reply that says `missing: ["category"]` is only useful if something remembers the conversation long enough to receive the answer. That is the next chapter.

---

## Where to go now

| Order | File | Track | What it is |
|---|---|---|---|
| 1 | [`EXERCISES.md`](EXERCISES.md) | 1️⃣ Drills | Rotating domains — weather, recipes. Never expenses |
| 2 | [`PROJECT.md`](PROJECT.md) | 2️⃣ + 3️⃣ | **Spendly Lite v3** and your own agent's v3 |
| 3 | [`../SDK_BRIDGE.md`](../SDK_BRIDGE.md) | — | Our code → SDK abstraction |
| — | `exercises/` | — | **Your** workspace, wired into the gate |
| — | `solutions/` | — | Reference builds. **Open after you attempt.** |
