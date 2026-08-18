# Chapter 4 — Sessions & State 🧠

> **Chapter 3 ended by asking a perfect question nothing could hear the answer to.**
>
> ```
> CASE 8  "Log 500 at Metro."
>         branch=need_more_info   missing=['category']
> ```
>
> The agent knew exactly what it was missing and asked for exactly that. Then the run
> ended, the process forgot everything, and the user's reply — `"Groceries."` — arrived
> at an agent that had never heard of Metro.
>
> A typed question is worthless if nothing survives to receive the answer.

| | |
|---|---|
| **Axis** | 🧠 State |
| **Depth** | 🚀 SDK-native only — no `from_scratch/`, no spike, by policy |
| **Budget** | **Core ≈ 10.5 hrs** · Full ≈ 16 hrs |
| **Sessions** | 2–3 sessions of 90–120 min |
| **Builds on** | Ch3's `replies.py` and Ch2's tools, imported unchanged |

---

## The first chapter with nothing to hand-roll

Three chapters have trained you to expect a `from_scratch/` folder. There isn't one, and
that is a decision rather than an omission.

The depth policy in `CLAUDE.md` asks one question before any spike: **what will the
student be unable to debug if we skip this?** For this chapter's two mechanisms, the
honest answer is *nothing*.

| Mechanism | Why it is not hand-rolled |
|---|---|
| `SQLiteSession` | It is a table with `session_id`, `message_data`, and an autoincrementing id. Rebuilding it teaches SQL, not agents. You already hand-built the *list* it stores — in Chapter 1 |
| `RunContextWrapper` | It is a Python object passed as an argument. There is no mystery to dispel, and pretending otherwise would be theatre |

What replaces the spike is one **📖 Observe** block — §2 — where you print what a session
stores and read it next to the `messages` list you built by hand in Chapter 1. They are
the same list.

> A chapter with no hand-rolled layer is not a lighter chapter. It is a chapter whose
> difficulty has moved from *building the mechanism* to *knowing when it lies to you*.
> §8 is the hardest page in this chapter, and it contains no new API at all.

---

## The one sentence to memorise

> **A session is what the agent remembers. A context is what you hand it.**

|  | `SQLiteSession` | `RunContextWrapper` |
|---|---|---|
| Holds | conversation history | your app's dependencies |
| Model sees it | **yes** — it *is* the messages | **no** — never serialised |
| Lives | across runs, on disk | one run, in memory |
| Grows | forever | not at all |
| Wrong use | putting an API key in it | expecting it to remember last turn |

Students conflate these two constantly, which is exactly why they are one chapter. You
cannot describe the difference convincingly until you have seen both fail in the other's
costume — and §1 opens with precisely that.

---

## Budget

Every section is marked `[core]` or `[depth]`. A student on the core path can skip every
`[depth]` block and still meet Chapter 5's prerequisites. The header equals the sum.

| § | Section | Tier | Min |
|---|---|---|-----|
| 1 | The bug that looks like memory | `[core]` | 25 |
| 2 | What a session actually is | `[core]` | 35 |
| 2b | Editing history by hand | `[depth]` | 30 |
| 3 | Wiring it in: one argument | `[core]` | 30 |
| 4 | `session_id` is the boundary | `[core]` | 30 |
| 5 | The context object | `[core]` | 45 |
| 5b | Typing the context properly | `[depth]` | 25 |
| 6 | Two users, one agent | `[core]` | 40 |
| 7 | Session vs context, and the two wrong uses | `[core]` | 25 |
| 8 | Stale state — the bug persistence *causes* | `[core]` | 45 |
| 9 | A session only grows | `[core]` | 30 |
| 9b | What a session is *not* | `[depth]` | 20 |
| 10 | Blank-file drill | `[core]` | 60 |
| | **README subtotal** | | **core 365 / full 440** |
| | `EXERCISES.md` — 4 core drills, 3 depth | | core 150 / full 300 |
| | `PROJECT.md` — Track 2 (60) + Track 3 (60), 3 challenges | | core 120 / full 210 |
| | **CHAPTER TOTAL** | | **core 635 min ≈ 10.5 hrs / full 950 min ≈ 16 hrs** |

---

## Setup

```powershell
uv sync
uv run python -m shared.models     # confirm your provider, costs nothing
```

Everything in this chapter runs free on Gemini. Three scripts make live calls; the rest
of the observation work re-reads what those scripts already stored, and costs nothing.

> ⚠️ **This chapter's demos hit a limit the earlier ones did not.** `session_demo.py`
> fires seven runs back to back, which is ~15 requests inside a minute — the
> **per-minute** free-tier cap. The golden datasets pause between cases and hit the
> **per-day** cap instead. Same status code, same exception class, completely different
> fix. **Read the `quotaId` in the 429 before you change anything.**

---

## §1 — The bug that looks like memory `[core]` · 25 min

Before adding memory, watch an agent appear to have it without having any.

```powershell
uv run python 04_sessions_state/with_sdk/session_demo.py
```

Parts 1a and 1b run **the same two prompts** at a packing-assistant agent, with **no
session** in either case. The only difference is whether the `Traveller` context object
is rebuilt between runs.

**Predict before you scroll.** Turn 2 is `"Add two more of those."` Write down what each
part does, and rate your confidence 1–5.

<details>
<summary>What actually happened (real output)</summary>

```
PART 1a - NO SESSION, FRESH CONTEXT. The true control.
  USER  : Pack two t-shirts, they're 0.2 kg each.
        -> add_item({"item":"t-shirt","kg":0.2})
        -> add_item({"item":"t-shirt","kg":0.2})
  AGENT : Both t-shirts have been packed.
  bag   : [('t-shirt', 0.2), ('t-shirt', 0.2)]
  USER  : Add two more of those.
        -> whoami({})
        -> show_list({})
  AGENT : What would you like to pack two more of?
  bag   : []

PART 1b - NO SESSION, SHARED CONTEXT. Watch this carefully.
  USER  : Pack two t-shirts, they're 0.2 kg each.
        -> add_item({"item":"t-shirt","kg":0.2})
        -> add_item({"kg":0.2,"item":"t-shirt"})
  AGENT : Both t-shirts have been packed.
  USER  : Add two more of those.
        -> whoami({})
        -> show_list({})
        -> add_item({"kg":0.2,"item":"t-shirt"})
        -> add_item({"kg":0.2,"item":"t-shirt"})
  AGENT : I've added two more t-shirts to your bag.
```

</details>

Look at the tool calls, not the replies. **Both parts called `show_list()`.** In 1a it
returned an empty bag and the agent honestly gave up. In 1b it returned two t-shirts, and
the agent reconstructed `"those"` from the *contents of the suitcase* rather than from
any memory of the conversation.

> **That is state leaking through the other primitive**, and it is the single most common
> reason people conclude they don't need sessions. It is not memory. The agent cannot
> recover anything a tool does not expose, cannot tell you what you **asked**, and cannot
> tell you what it **refused**. A session can do all three.

**This part was an accident.** The first version of `session_demo.py` shared the context
by mistake, and its output was convincing enough that it nearly shipped as proof that
sessions are unnecessary. It is kept deliberately, because your students will make the
same mistake.

### 🔨 Practice 1 (10 min)

Break 1b's illusion without adding a session. In `packing_agent.py`, comment `show_list`
out of the `tools=[...]` list and re-run.

**You're done when** part 1b's second turn can no longer name the item, and you can state
in one sentence why removing a *tool* changed what the agent appeared to *remember*.

---

## §2 — What a session actually is `[core]` · 35 min 📖 Observe

Run the same script and read **PART 2**. Three turns, one `SQLiteSession`, and then every
stored item printed.

```
    [ 0] user                         Pack two t-shirts, they're 0.2 kg each.
    [ 1] function_call:add_item       {"item":"t-shirt","kg":0.2}
    [ 2] function_call_output         Packed t-shirt (0.2 kg). Bag now 0.2 kg.
    [ 3] function_call:add_item       {"item":"t-shirt","kg":0.2}
    [ 4] function_call_output         Packed t-shirt (0.2 kg). Bag now 0.4 kg.
    [ 5] assistant                    I've packed both t-shirts for you.
    [ 6] user                         Add two more of those.
    [ 7] function_call:add_item       {"item":"t-shirt","kg":0.2}
    [ 8] function_call_output         Packed t-shirt (0.2 kg). Bag now 0.6 kg.
    [ 9] function_call:add_item       {"item":"t-shirt","kg":0.2}
    [10] function_call_output         Packed t-shirt (0.2 kg). Bag now 0.8 kg.
    [11] assistant                    I've added two more t-shirts.
    [12] user                         What's in the bag?
    [13] function_call:show_list      {}
    [14] function_call_output         t-shirt (0.2 kg); ...
    [15] assistant                    You have four t-shirts in your bag.
```

Now open `01_agent_loop/from_scratch/agent.py` beside it and find the line where you did
this by hand:

```python
messages.append({"role": "user", "content": prompt})
```

**It is the same list.** Same roles, same tool-call/tool-output pairing, same
append-only growth. The script even prints the raw JSON of item 0 so there is nowhere for
magic to hide:

```json
{"content": "Pack two t-shirts, they're 0.2 kg each.", "role": "user"}
```

The three facts worth carrying forward:

1. **A tool call and its result are two separate items.** That pairing matters in §9.
2. **Every turn appends; nothing is ever removed.** That is §9's whole argument.
3. **The word `Faraz` is nowhere in the list**, even though the run had a `Traveller`
   named Faraz attached. That is §5.

### 🔨 Practice 2 (12 min)

Add a fourth turn to `TURNS` that makes the agent *refuse* something — ask it to pack an
item with a negative weight. Re-run and find the refusal in the item list.

**You're done when** you can point at the stored items and say which one the model will
read on turn 5 to know it already refused. This is the thing §1b's context leak could
never do.

---

## §2b — Editing history by hand `[depth]` · 30 min

`SQLiteSession` gives you four methods, and two of them are write operations you will
eventually need in a product:

| Method | What it is for |
|---|---|
| `get_items(limit=None)` | read the transcript |
| `add_items(items)` | inject turns that never happened — seeding, replay, testing |
| `pop_item()` | remove the newest item |
| `clear_session()` | empty it without deleting the database |

`pop_item()` exists for a specific, unglamorous reason. `Runner.run` writes the user's
message into the session **as the run starts**, so a run that dies mid-flight leaves it
behind — and a naive retry then makes the user appear to say the same thing twice.

Read `_run_with_backoff` in `solutions/expense_agent_v4.py`. It documents that hazard and
then deliberately does **not** repair it, because a test harness that repairs the thing
it is testing is not a test harness. In a product, you repair it.

### 🔨 Practice 2b (18 min)

In `solutions/test_context.py`, `test_pop_item_removes_the_newest_item` proves the newest
item goes first. Write a test that seeds a session with `add_items` so an agent starts a
conversation already believing something — then assert `get_items()` returns it.

**You're done when** it passes with no API key, and you can name one product feature this
enables (hint: "resume where you left off after a deploy").

---

## §3 — Wiring it in: one argument `[core]` · 30 min

Here is the entire code change that gives Spendly a memory:

```python
result = await Runner.run(agent, prompt, session=session)
#                                        ^^^^^^^^^^^^^^^
```

That is it. Now run the spine and watch Chapter 3's unanswerable question get answered:

```powershell
uv run python 04_sessions_state/solutions/expense_agent_v4.py
```

```
TURN 1  USER: Log 500 at Metro.
  branch        : need_more_info
  session items : 2
  input tokens  : 1851
  reply         : NeedMoreInfo(question='Which category does this expense belong to?',
                               missing=['category'])

TURN 2  USER: Groceries.
  -> log_expense({"category":"Groceries","amount":500,"vendor":"Metro","expense_date":""})
  branch        : logged
  session items : 6
  input tokens  : 3940

ledger now holds 1 new row(s):
  [{'vendor': 'Metro', 'amount': 500.0, 'category': 'Groceries', ...}]
```

**The user typed one word and a complete expense appeared.** The vendor and the amount
came from a turn that had already ended.

### What did *not* change, and why that is the lesson

Open `expense_agent_v4.py` and diff it against Chapter 3's v3. The prompt gained **no**
instruction to "remember the conversation" — there is nowhere useful to put one. The
model does not choose to remember. The session puts the previous turns back into the
request, and a model that can read its own transcript needs no encouragement.

Compare that with Chapter 3, where `output_type=` handled the *shape* and four paragraphs
of prompt handled the *judgement*, because branch selection genuinely is a judgement.

> **Ask this of every new primitive: does it replace a rule I was writing in English?**
> If yes, delete the English. If no, the prompt still owns that job. Getting this wrong
> in either direction is how prompts become 900 lines of contradictions.

### 🔨 Practice 3 (15 min)

Add a third turn to `main()`: `"Actually make that 700."` Run it.

**You're done when** you can say whether the agent edited the existing row, logged a
second one, or refused — and whether the tools you have make the right answer even
*possible*. (They do not. That gap is deliberate; it becomes Exercise 3.)

---

## §4 — `session_id` is the boundary `[core]` · 30 min

Run **PART 3** of `session_demo.py`, and **PART 2** of `growth_demo.py`. Together they
teach one thing: the isolation between two conversations is a string and a file path, and
nothing checks either one.

```
  SQLiteSession('growth_demo', DB_PATH)  ->  22 items
  SQLiteSession('growth_demo')           ->   0 items
```

Identical `session_id`. One holds the conversation, one is empty, **and neither raised an
error.** The id names a *row*; `db_path` names the *book* it is a row in — and `db_path`
defaults to `":memory:"`, a database that lives inside one Python object and dies with it.

> **This is a bug with a schedule.** It works perfectly all through development, because
> a dev server is one process holding one object. It fails the moment you run two
> workers, restart on deploy, or scale to two pods — and it fails as *"the agent forgot
> everything"*, which reads like a model problem and sends you debugging the prompt.

The mirror failure is worse. Two conversations that **share** an id are one conversation:

- `session_id = username` → a user with two browser tabs is one confused conversation
- `session_id` from a customer-supplied string → one customer can read another's history

🔒 **Trust axis.** `session_id` is an authorisation decision wearing the costume of a
cache key. Derive it server-side from something the user cannot choose.

### 🔨 Practice 4 (15 min)

In `test_context.py`, read `test_two_sessions_with_the_same_id_can_be_different_conversations`.
Now write its dangerous sibling: two sessions with the same id **and** the same
`db_path`, and assert that the second one can read the first's messages.

**You're done when** the test passes and you have written one sentence naming a real
product where that assertion is a data breach.

---

## §5 — The context object `[core]` · 45 min

A session answers *"what has been said?"*. It cannot answer *"who is asking?"* — and
putting the answer in the session would be wrong on three counts: you would pay for it in
tokens on every turn, expose it to anyone who can make the model repeat its instructions,
and let the model round it.

```python
@function_tool
def get_budget(ctx: RunContextWrapper[User], category: Category) -> float:
    """Get the monthly budget in PKR for one category."""
    return ctx.context.budget_for(category)
```

```powershell
uv run python 04_sessions_state/with_sdk/context_demo.py
```

**PART 1 costs nothing** and settles the central claim by printing the schemas the model
actually receives:

```
  whoami                 model is told about: (no arguments)
  add_item               model is told about: ['item', 'kg']
  remaining_allowance    model is told about: (no arguments)

  whoami's full schema: {"properties": {}, "title": "whoami_args",
                         "type": "object", "additionalProperties": false, "required": []}
```

All three functions declare `ctx: RunContextWrapper[Traveller]` as their first parameter.
**Not one of them mentions it.** The SDK strips a leading `RunContextWrapper` before
generating the tool definition.

> That asymmetry is the whole primitive. The model decides **what** to ask for; your
> application decides **whose data** answers. Neither can see the other's input — which
> means a prompt injection cannot reach `ctx.context` no matter how it is worded. **There
> is no argument to poison.**

### The half everybody skips

Run **PART 3**:

```
  PART 2's session for Faraz: 6 items
  does the transcript contain the string 'Faraz'? -> True

  a run that never called whoami: 4 items
  does THAT transcript contain 'Faraz'? -> False
```

The context did not leak on its own. It left the process because a **tool returned it**,
and a tool's return value is stored in the session like everything else.

> **A context is private until a tool returns part of it. After that it is in the
> transcript, permanently, and re-sent on every subsequent turn.**

Which makes *"what does this tool return?"* a security question, not an API-design one.
Returning a whole context object from a convenience tool is how a support agent ends up
with a customer's internal risk score in a transcript somebody later exports.

### 🔨 Practice 5 (18 min)

Add a `notes: str` field to `Traveller`, set it to something you would not want printed,
and write a tool `trip_summary()` that returns `str(ctx.context)`. Run one turn with a
session, then dump `session.get_items()`.

**You're done when** you can find the secret in the transcript, and have fixed the tool so
it returns only what the model needs.

---

## §5b — Typing the context properly `[depth]` · 25 min

```python
agent = Agent[User](name="Spendly Lite v4", ...)
```

At runtime the `[User]` changes **nothing**. At edit time it is the difference between
pyright checking `ctx.context.budget_for(...)` and pyright shrugging, because an
unparameterised `Agent`'s context is `Any` — and `Any` accepts every typo you will ever
write.

### 🔨 Practice 5b (25 min)

Change `Agent[User]` to `Agent`, then write `ctx.context.buget_for(category)` (note the
typo) in `get_budget`. Run `uv run pyright`. Restore the `[User]` and run it again.

**You're done when** you have seen pyright stay silent in one case and catch it in the
other, and can explain why "the SDK is fully typed" is only half the story — *you* supply
the other half.

---

## §6 — Two users, one agent `[core]` · 40 min

The measured payoff. `context_demo.py` PART 2 sends **one identical prompt** to **one
agent object** twice:

```
  prompt (identical for both): 'Who am I packing for, and how much room do I have left?'

  context = Traveller(name='Faraz', bag_limit_kg=20.0)
  AGENT   : You're packing for Faraz, and you have 18.6 kg left.

  context = Traveller(name='Ayesha', bag_limit_kg=7.0)
  AGENT   : You are packing for Ayesha, and you have 5.6 kilograms remaining.
```

Same agent. Same instructions. Same tools. Same prompt string. **One keyword argument
different, two different correct answers.**

On the spine, `spendly_context.py` does the same thing to a rule that has been a *law*
since Chapter 1. `MONTHLY_BUDGETS` was a module-level dict, which quietly asserted that
every user of Spendly has the same budget — true only because there was one user and they
were hard-coded.

```
Chapters 1-3   get_budget(category)        -> MONTHLY_BUDGETS[category]
Chapter 4      get_budget(ctx, category)   -> ctx.context.budget_for(category)
```

Golden-dataset case **M5** asserts both answers: `17500` for Faraz, `1500` for Ayesha,
from the same question against the same ledger.

### What did *not* move, and why that is the interesting half

The **ledger** did not move. Expenses still live in `expense_store`, shared.

> A **context** holds what your app knows about *this run* — who is asking.
> A **store** holds what your app knows, *period* — what happened.

A budget is configuration attached to a person. An expense is a fact about the world. Put
facts in a context and you will end up passing your database around as an argument; put
configuration in a store and you will end up adding a `user_id` column to a settings
table.

### 🔨 Practice 6 (20 min)

Add a third user to `spendly_context.py` with a food budget of exactly `7500` — the
seeded month's total. Run one turn asking what's left.

**You're done when** you can state what `remaining == 0` should mean to the caller, and
whether `Reported.remaining` being `0.0` is distinguishable from it being *unset*. (Look
at the field's type in `replies.py` before answering.)

---

## §7 — Session vs context, and the two wrong uses `[core]` · 25 min

You have now seen both fail in the other's costume:

- **§1b** — a *context* leaked and looked like memory
- **§4** — a *session* silently didn't persist and looked like amnesia

|  | `SQLiteSession` | `RunContextWrapper` |
|---|---|---|
| Holds | conversation history | your app's dependencies |
| Model sees it | **yes** | **no** — until a tool returns part of it |
| Lives | across runs, on disk | one run, unless you keep the reference |
| Grows | forever | not at all |
| Scoped by | `session_id` + `db_path` | the object you pass to `context=` |

### The two wrong uses, named

**Putting a credential in a session.** Everything in a session is sent to the model on
every turn, and stored on disk in plaintext. An API key in a session is an API key in
your transcript exports.

**Expecting a context to remember last turn.** It holds whatever object you passed. If you
construct a fresh one per request — as any web handler will — it holds nothing from
before. §1b's illusion happens when you *don't*, and that illusion is not a feature you
can rely on.

> The rule that survives both: **a context may HOLD a database handle. It must never HAND
> one out.**

### 🔨 Practice 7 (12 min)

Write down, for your own Track 3 agent, one piece of state currently in your prompt that
belongs in a context, and one currently in a context that belongs in a store. One sentence
each on how you can tell.

**You're done when** you have both, and neither answer is "it doesn't matter".

---

## §8 — Stale state: the bug persistence *causes* `[core]` · 45 min

**This is the chapter's §7b — the honest limitation, in the tradition Ch2 and Ch3
established.** Every chapter so far narrowed a failure without closing it:

| Chapter | The rule | What it still cannot stop |
|---|---|---|
| 2 §7b | a type makes a bad value impossible to *accept* | the model **fabricating** a good one |
| 3 §8 | a schema makes a bad answer impossible to *hide* | a **well-formed false** one |
| **4 §8** | a session makes context impossible to *lose* | the model **reciting** a fact that has since changed |

Chapter 1's rule was *"use tools for every fact, never recall from memory."* That was easy
to keep when **there was no memory to recall from.** A session is what makes it hard —
because now there genuinely is a plausible-looking number sitting in the transcript, in
the agent's own handwriting.

Golden-dataset case **M4** is built exactly around this:

```
TURN 1   "How much have I spent on food this month?"
         -> month_total()  ->  7500       agent replies "7500"

         [ the world changes: 5000 of food spending arrives from
           the mobile app / a bank sync / a shared household ledger ]

TURN 2   "And how much now?"
         must be 12500. The cheap wrong answer, 7500, is written
         in the agent's own words two items up the transcript.
```

The harness writes that expense with `expense_store.append(...)` and never tells the
agent. That is not a contrivance — it is Tuesday. **Any product with more than one entry
point has this, and an agent holding a conversation is by definition holding a stale copy
of everything it was told.**

Which layer owns the fix? Work through the four:

| Layer | Can it stop a stale recital? |
|---|---|
| A **type** | No. `12500` and `7500` are both valid floats |
| A **schema** | No. The reply's shape is flawless either way |
| A **cross-check** | Yes — re-read the value after the model speaks and compare |
| A **prompt** | Only lowers the rate |

v4's prompt takes the prompt-shaped part of the job explicitly:

```
- A figure from earlier in this conversation is not a fact, it is a quote. If the
  ledger has changed since -- or if you are not certain it has not -- call the
  tool again. Re-reading a number is cheap; reporting a stale one is not.
```

And M4 asserts the behaviour rather than trusting the sentence: `"month_total" in
run.executed_names` proves the tool was called **again on turn 2**, not that the number
merely happened to be right.

> **Assert the route, not just the destination.** An agent that guesses `12500` correctly
> and an agent that re-reads it are the same on one case and different on a hundred.

### 🔨 Practice 8 (25 min)

Run only that case:

```powershell
uv run python 04_sessions_state/solutions/check_multiturn.py --only 4
```

Then delete the `PERSONAL BUDGETS` paragraph from `SYSTEM_PROMPT` and run it **three
times**.

**You're done when** you can report how many of three runs recited the stale number — and
can say why "it passed once" is not evidence of anything. Record the result in
`solutions/RUNS.md`.

---

## §9 — A session only grows `[core]` · 30 min

```powershell
uv run python 04_sessions_state/with_sdk/growth_demo.py
```

Five turns, one session, measured:

```
  turn    items   history   reqs   in tok  tok/req   agent
  ----------------------------------------------------------------------------
  1           6     1,377      3    1,203      401   I've packed both t-shirts...
  2          10     2,257      2    1,017      508   I've added the jeans to y...
  3          14     3,106      2    1,167      584   I've packed the jacket.
  4          18     3,975      2    1,309      654   I've packed the hiking bo...
  5          22     4,782      2    1,427      714   You have 16.1 kg remaining.
```

**Read `history`, not `in tok`.** The transcript went 1,377 → 4,782 characters in five
short turns and it is monotonic — that is arithmetic, not a tendency. `tok/req` climbs
with it, 401 → 714.

> **The first version of this table measured the wrong thing**, and the mistake is worth
> more than the table. It printed a turn-over-turn ratio of `in tok`, which came out
> around 1.1× and made the chapter's argument look weak. Two reasons:
>
> 1. `usage.input_tokens` is the **sum over every request the run made**. A turn with two
>    tool calls is three requests, so it out-totals a longer turn needing one. Divide by
>    `usage.requests` or you are measuring tool chattiness, not history.
> 2. At turn 5 the **fixed** cost dominates — system prompt plus four tool schemas is
>    roughly a thousand tokens before the conversation says anything.
>
> That second point *is* the warning. The bill does not arrive as a cliff you can see
> coming. It arrives as a slope you cannot see at all until the fixed cost stops being the
> biggest number — which is exactly why *"we'll add trimming when it becomes a problem"*
> is a plan that fails.

### The one knob, and its edge

`growth_demo.py` PART 3 is free — it re-reads what PART 1 stored:

```
  limit     items    chars   first item            orphaned?
  --------------------------------------------------------------
  2             2      372   function_call_output  YES
  3             3      745   function_call         no
  4             4      807   user                  no
  6             6    1,221   function_call_output  YES
  8             8    1,676   user                  no
```

`get_items(limit=N)` — or `SessionSettings(limit=N)` on the session — takes the **last N
items**. It is a tail window, not a summariser:

- the database still grows forever; `limit` changes what you **read**, never what you **store**
- it counts **items**, not tokens — one item can be four tokens or four thousand
- see the `orphaned?` column: a window can start on a tool **result** whose **call** was
  cut away. Some providers reject that outright
- the oldest turn is usually where the user said what they **want**. A tail window throws
  away precisely the wrong end

> The SDK hands you a chainsaw and correctly declines to decide how to swing it.

**That decision is Chapter 5.** Trimming on tokens rather than items, keeping call/result
pairs together, summarising the head instead of dropping it — every one of those is a
design choice this chapter has just made unavoidable.

### 🔨 Practice 9 (15 min)

Extend `TURNS` in `growth_demo.py` to twelve entries. Before running, predict `history`
at turn 12 by extrapolating the table above; then run it and compare.

**You're done when** your prediction is within 20%, and you can name the turn number at
which history overtakes the fixed prompt cost.

---

## §9b — What a session is *not* `[depth]` · 20 min

A session is a **transcript**, not a memory, and the difference bites in three ways:

1. **It remembers wrong things as faithfully as right ones.** If the agent hallucinated a
   number on turn 2, turn 20 will cite it with total confidence — it is in the record, in
   its own handwriting. A session gives your agent a memory; it does not give it a *good*
   memory.
2. **It cannot answer "what do we know about this user?"** — only "what was said in this
   conversation?". Those diverge the moment a user has two conversations.
3. **It is not searchable.** Nothing retrieves the relevant turn from turn 400. That is
   retrieval, and it is a different primitive.

### 🔨 Practice 9b (20 min)

Write down three facts your Track 3 agent should know about a user **across** conversations.
For each: session, context, or store? Justify the ones that are not obvious.

---

## §10 — Blank-file drill `[core]` · 60 min — **mandatory**

> **Recognition, recall and generation are three different competencies.** Everything
> above this line was reading and modifying. This is the one that proves fluency.

Open an empty file. No copying from this chapter. Unfamiliar domain, deliberately.

**Build: a clinic appointment assistant.**

Requirements:

1. A `Patient` context object carrying `patient_id`, `name`, and `visits_remaining` on
   their insurance plan
2. At least three tools; **at least two must read the context**
3. A `SQLiteSession` keyed per patient, file-backed
4. A conversation that only works multi-turn — turn 2 must depend on turn 1
5. One tool that **deliberately does not** return the patient's name, and a comment saying
   why
6. Print the session's item count after each turn

**You're done when:**

- [ ] It runs with `uv run python <yourfile>.py`
- [ ] Turn 2 completes an action using a value supplied only in turn 1
- [ ] Two patients with different `visits_remaining` get different answers to the same prompt
- [ ] You can point at the stored items and say which one turn 3 will read
- [ ] `uv run ruff check` and `uv run pyright` are clean on it

Reference solution: `solutions/` — **after** you attempt it, not before.

---

## Prove it — the two datasets

```powershell
uv run pytest 04_sessions_state -q                                    # free, ~1s
uv run python 04_sessions_state/solutions/check_multiturn.py          # ~11 min
uv run python 04_sessions_state/solutions/check_regression.py         # ~15 min
```

### M2 is the case that earned its keep

The control looks like padding until it isn't. On one verification run it failed — and
what it caught was a defect introduced **by the fix that made M1 pass**.

`USING WHAT YOU WERE ALREADY TOLD` was added to the prompt so a one-word `"Groceries."`
would complete the expense from turn 1. It did. It also told the agent, when run with
*no* session, that a one-word reply must be answering a question it had asked — so it
called `log_expense` with a vendor and an amount nobody had ever given it.

```
CASE M2  TURN 2  "Groceries."      (no session)
  FAIL  the agent wrote nothing to the ledger
  FAIL  log_expense never executed
  branch=logged   turns=8
```

> **A rule written to exploit memory becomes an instruction to invent when the memory is
> absent.** Every test that had a session passed. The rule never said *"check that you can
> actually see it"* — it did not need to, until something ran without a transcript.

That is the fourth member of the family this curriculum keeps narrowing:

| Where | The model… |
|---|---|
| Ch2 §7b | **fabricated** a value from nothing |
| Ch3 §1 | **miscomputed** one from real tool output |
| Ch3 case 8 | **inferred** a plausible one from context |
| **Ch4 M2** | **backfilled** one from a conversation that never happened |

The fix is a prompt fix, correctly — the reply was a flawless `Logged`. Only the world it
described was imaginary, and no schema can object to that.

**So: an eval with no control cannot tell "the session works" from "the model guessed
well" — and it also cannot tell you when the thing you added to make the session work has
quietly taught the agent to lie without one.**

---

**Two harnesses, deliberately.** A 2-turn case costs roughly twice the requests of a
1-turn case; folding five of them into Chapter 3's nine takes one run from ~15 minutes to
~25 and roughly doubles the odds the free tier poisons it mid-flight — the exact failure
that cost a complete Chapter 3 run.

> **When an eval gets long enough to fail for infrastructure reasons, split it before you
> tune it.**

`check_regression.py` is the regression rule made executable. It imports **Chapter 3's
nine cases verbatim** and runs them through **Chapter 4's agent**:

```python
from check_expenses import CASES                   # Chapter 3's dataset, unmodified
from expense_agent_v4 import run_expense_agent     # this chapter's agent
```

Up to now the regression rule was enforced by re-running the old harness against the old
agent — which proves the old code still works and says nothing about the new code.

That file is forty lines instead of a forked dataset for exactly one reason: Chapter 3's
harness declared what it needed as a **`Protocol`**, not as its concrete `SdkRun` class.
At the time that looked like ceremony for no benefit. One chapter later it is why v4's
`SdkRun` — which grew two new fields — still satisfies every Chapter 3 check without
either file knowing the other exists.

> **Depend on the shape you need, not the class you happen to have.** You cannot predict
> which of your types will be replaced; you can make the replacement cheap.

---

## What this chapter cannot do — the hook for Chapter 5

§9 measured it and named it, so this is short.

**The session grows forever, and the only tool the SDK gives you is a tail window that
counts the wrong unit and can cut a tool call away from its result.**

Every turn appends. Nothing prunes. Twenty turns in you are re-sending the whole
conversation on every request, paying for it every time, and heading for a hard
context-length error that will arrive mid-conversation with a user watching.

**Chapter 5 — The Context Window** is that failure, and the strategies that survive it.

---

## 🔁 Spendly Transfer

In the real Spendly (`C:\Users\Faraz\Desktop\Spendly\`):

1. Add a `SQLiteSession` keyed by the WhatsApp phone number — **hashed, not raw** (§4:
   `session_id` is an authorisation decision)
2. Add a context object carrying the sender's timezone, and make one date-handling tool
   read it instead of assuming the server's clock
3. Log `len(await session.get_items())` per turn for one week and find your real p95

**You're done when** a user can send `"500 at Metro"` then `"groceries"` as two separate
WhatsApp messages and get one correctly logged expense.

---

## Where the pieces live

```
04_sessions_state/
  README.md                       this file
  with_sdk/
    packing_agent.py              the demo agent (non-expense, on purpose)
    session_demo.py               §1, §2, §4   -- what a session holds
    growth_demo.py                §4, §9       -- what a session costs
    context_demo.py               §5, §6       -- what the model cannot see
    compare.md                    Ch1's hand-built list -> the SDK's session
  solutions/
    _bootstrap.py                 the runtime sys.path shim (Ch3 explains it)
    spendly_context.py            the User context object
    expense_agent_v4.py           the spine: session + context
    check_multiturn.py            5 multi-turn cases
    check_regression.py           Chapter 3's 9 cases, against v4
    test_context.py               13 offline tests, no API key
    RUNS.md                       evidence
  EXERCISES.md                    Track 1 drills
  PROJECT.md                      Track 2 spine + Track 3 own agent
```
