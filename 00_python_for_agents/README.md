# Chapter 0 — Python for Agents

> **You know Python.** This chapter is not a Python course.
>
> It covers exactly six things that Chapter 1's *first file* already assumes, and nothing else. Every section ends by pointing at the line of real curriculum code where you'll meet it.

| Part | Core | Full |
|---|---|---|
| This README (§1–§6) | 4.5 hrs | 5.5 hrs |
| [`PROJECT.md`](PROJECT.md) — Name Check | 1.5 hrs | 2 hrs |
| **Chapter total** | **≈ 6 hrs** | **≈ 7.5 hrs** |

**Plan 2 sessions.** More than half the time is §5, and that is deliberate — async is the concept that most often gets skipped and then quietly breaks everything downstream.

---

## First: do you even need this chapter?

Six questions, one per section. **Write your answer down before running anything.**

```python
# 1
def first(items: list[str]) -> str | None: ...
x = first([])
print(x.upper())          # what does pyright say, and is it right?

# 2
@shout
def greet(): return "hi"  # rewrite these two lines WITHOUT using @

# 3
@dataclass
class Run:
    names: list[str] = []  # what is wrong with this line?

# 4
class M(BaseModel):
    x: int
print(M(x=True).x)         # what prints?

# 5
async def f(): return 1
print(f())                 # what prints?

# 6
def test_add():
    assert add(2, 2) == 5  # what does pytest print, and what is the exit code?
```

| Score | Do this |
|---|---|
| 6/6 | Skim the "where you'll meet this" boxes and go to Chapter 1 |
| 3–5 | Do only the sections you missed |
| 0–2 | Do the whole chapter. It will save you a week |

Answers are at the bottom. **Don't scroll yet** — a guess you commit to is worth ten you read.

---

## 1. Type hints that do work `[core]` · 60 min

Most Python courses teach type hints as documentation. In this curriculum they are **executable**: from Chapter 2 on, a type hint becomes a JSON Schema the model reads and a check that runs before your function body. So it is worth being fluent in the four that carry real weight.

```powershell
uv run python 00_python_for_agents/examples/foundations.py
uv run pyright 00_python_for_agents/examples/foundations.py
```

Run **both**. The second is the point — most of what hints buy you never appears at runtime. It appears in the errors you never get.

### The four that matter

**`list[Message]`, not `list`.** A bare `list` tells you nothing. The shape is what catches bugs.

**`X | None` — the most valuable hint you will ever write.** `AttributeError: 'NoneType' has no attribute ...` is the most common runtime error in Python, and it happens because some path returned `None` and nobody handled it. Writing `-> str | None` makes that path *the caller's problem, at edit time.*

**`Callable` — a type for functions themselves.** This is the one that makes an agent possible:

```python
REGISTRY: dict[str, Callable[..., float]] = {"add": add, "multiply": multiply}

function = REGISTRY[name]      # name came from a language model
result = function(**args)      # args came from a language model
```

That is a tool registry. Chapter 1's is about four lines longer.

**`cast()` — telling the checker something it can't work out.** It changes *nothing* at runtime; it's you making a promise. Use it where a library's types are weaker than its guarantees, never to silence an error you haven't understood.

### ▶ Practice 1 — break it on purpose (20 min)

In `foundations.py`, uncomment the `print(found.upper())` line and run `pyright`.

1. Read the error. Is pyright right? Construct the input that would actually crash.
2. Fix it three ways: an `if` guard, a default return, and `assert found is not None`. Which is honest, and which is hiding something?
3. Change `REGISTRY`'s type to `dict[str, Callable[[float, float], float]]` and run pyright again. Read the new error — and then read the comment above `REGISTRY` explaining why it says `...` instead.

**You're done when:** you can say what `cast()` costs you, and why `assert x is not None` is not always the honest fix.

> **📍 Where you'll meet this:** `01_agent_loop/from_scratch/agent.py` — `list[ChatCompletionMessageParam]`, `TOOL_REGISTRY: dict[str, Callable]`, and exactly one `cast()`, on line 89.

---

## 2. Decorators `[core]` · 45 min

You will meet `@tool`, `@function_tool`, `@dataclass`, `@property`, `@model_validator` and `@input_guardrail`. All of them are one idea.

> ### 🧠 The whole feature, in one line
>
> ```python
> @shout
> def greet(): ...
> ```
>
> is *literally* shorthand for:
>
> ```python
> def greet(): ...
> greet = shout(greet)
> ```
>
> A decorator is a function that takes a function and returns something. That's it. Everything else is what you put inside.

```powershell
uv run python 00_python_for_agents/examples/decorator_lab.py
```

Four demos: the shorthand proved, a decorator that adds timing, the `functools.wraps` bug, and — the one that matters — a **registry decorator**:

```python
TOOLS: dict[str, Callable[..., Any]] = {}

def tool(fn):
    TOOLS[fn.__name__] = fn
    return fn            # returns it UNCHANGED
```

Note what that does *not* do. It doesn't wrap, modify or slow the function down. It's pure side effect — put an entry in a dict, hand the function back. That's a completely legitimate decorator and it's most of what Chapter 2's `@tool` does.

### The bug you'd otherwise ship

A wrapper without `@functools.wraps(fn)` **silently loses the function's name and docstring**. Run the lab and look at demo 3.

Now put that next to how tools work here: `@function_tool` reads your docstring and sends it to the model as the tool's description. A decorator that eats the docstring produces a tool the model can't understand — and *nothing crashes*. The agent just gets quietly worse at choosing it.

### ▶ Practice 2 — write two (25 min)

1. Write `@retry` — calls the function, and if it raises, tries twice more before giving up. Test it with a function that fails the first two times.
2. Write `@count_calls` — remembers how many times it was called, exposed as `fn.calls`.
3. Deliberately omit `functools.wraps` from one of them and print `__name__` and `__doc__`.

**You're done when:** both work, and you can explain why `@retry` needs `*args, **kwargs` but the registry decorator doesn't.

> **📍 Where you'll meet this:** `02_typed_tools/from_scratch/typed_tool.py` — `@tool` does exactly the registry trick, plus reading the signature to build a schema.

---

## 3. Dataclasses `[core]` · 30 min

**The problem:** a function with several things to tell you.

```python
return answer, tools_used, iterations, hit_limit
```

Now every caller unpacks four values in the right order, forever. Add a fifth and every call site breaks. And `result[2]` tells the next reader nothing.

```python
@dataclass
class RunReport:
    final_answer: str
    iterations: int = 0
    tool_names: list[str] = field(default_factory=list)

    @property
    def used_tools(self) -> bool:
        return len(self.tool_names) > 0
```

You wrote no `__init__`, no `__repr__`, no `__eq__`. That's the pitch: a dataclass is a class whose job is to hold named values.

### The trap worth meeting once

```python
tool_names: list[str] = []          # WRONG — and Python will not stop you
```

That list is created **once**, when the class is defined, and every instance shares it. Appending to one report's list appends to all of them. `field(default_factory=list)` says "call this to make a fresh one per instance."

### ▶ Practice 3 — feel the shared-list bug (20 min)

1. Change `RunReport.tool_names` to `= []`. pyright will complain — read what it says, then make it run anyway.
2. Create two reports, append to one, print both.
3. Restore `default_factory`. Confirm it's fixed.
4. Add a `@property` called `summary` returning `"3 iterations, 2 tools"`.

**You're done when:** you've seen one object's append show up in another, and can say why `@property` is read without parentheses.

> **📍 Where you'll meet this:** `AgentRun` in every chapter's `loop.py`, with `@property` for `executed_names` and `rejected_count`.

---

## 4. Pydantic `[core]` · 60 min

Every value an agent hands your code was written by a language model. It's text, it's untrusted, and it's *usually* fine — which is the dangerous kind of wrong in a program that writes to a database.

```powershell
uv run python 00_python_for_agents/examples/pydantic_lab.py
```

### What a rejection gives you

```
3 problems, all reported at once:

  passenger  String should have at least 1 character  (you sent: '')
  seats      Input should be less than or equal to 9  (you sent: 40)
  cabin      Input should be 'economy', 'business' or 'first'  (you sent: 'premium')
```

All the problems, not just the first. Each names the field, the rule and the value you sent. And nothing after the validation ran, so nothing is half-done.

In Chapter 2 you turn exactly this structure into a message a **model** reads and acts on. *An error is an instruction when the reader is an agent* — that reframing is most of the chapter.

### Coercion: helpful, then a menace

```python
seats: "3"     ->  3      # good — models put numbers in quotes constantly
seats: true    ->  1      # ...oh
```

`true` passed a check for a whole number between 1 and 9, because in Python `bool` is a subclass of `int`. No rule was broken. You have a confirmed booking for one seat nobody asked for, and nothing will ever flag it.

> **This is a real bug this repository shipped.** Chapter 2 accepted `{"amount": true}` and logged an expense of PKR 1.00. It was caught by a test, not by reading.
>
> The lesson to carry forward: **a library's defaults are somebody else's judgement about your trade-offs.** Lax coercion is right for a model's sloppy JSON and wrong for a money field, and only you know which one you have.

### ▶ Practice 4 — design a model (30 min)

Write `SignupForm` with: `username` (3–20 chars, lowercase/digits/underscore), `age` (13–120), `plan` (one of free/pro/team), `referral_code` (optional).

Then attack it with six payloads — an empty username, age as `"25"`, age as `true`, a plan of `"Pro"`, a missing field, and an extra field nobody asked for.

**You're done when:** you can predict all six outcomes before running, and you have an opinion on whether `"Pro"` *should* be rejected.

> **📍 Where you'll meet this:** `02_typed_tools/solutions/expense_tools.py` — `Amount`, `Vendor`, `IsoDate`, and the `BeforeValidator` that fixes the bool trap.

---

## 5. `async` / `await` `[core]` · 75 min — **the big one**

Async is the concept most people skip and then quietly suffer. It's worth slowing down for, so this section is a lab, not a lecture.

> ### 🧠 Mental model: one person, several machines
>
> You're doing laundry. **You have one pair of hands.**
>
> ```
> You load the washing machine and press start.   <- takes you 5 seconds
> The machine now runs for 30 minutes.            <- takes you NOTHING
> ```
>
> The question that decides everything: **what do you do during those 30 minutes?**
>
> - **Synchronous you** sits in front of the machine and watches it.
> - **Asynchronous you** goes and loads the dishwasher, then answers an email.
>
> Both of you have exactly one pair of hands. Neither does two things at the same instant. The async version isn't faster at any single task — it's faster overall because it **stopped treating waiting as working**.

Map it and every keyword lands:

| Code | Laundry |
|---|---|
| `async def wash()` | this job has waiting in it |
| `await machine` | "the machine is running; I'm free — someone else go" |
| `asyncio.run(...)` | **you**. Somebody has to do the walking around |
| `asyncio.gather(...)` | start the washer *and* the dishwasher before waiting on either |
| folding clothes | no waiting, only hands. Nothing to hand off — this is CPU work |

### The lab

```powershell
uv run python 00_python_for_agents/examples/async_lab.py       # all six
uv run python 00_python_for_agents/examples/async_lab.py 3     # just one
```

Six experiments, each killing one misconception. **Predict the timing before each.**

#### 1 — Calling an async function does not run it

```
check_domain('spendly')  ->  <coroutine object check_domain at 0x...>
```

You didn't get a string. You got a **coroutine object**: a job described and not started. It's a written note saying *"wash the towels"* — writing the note is not doing the laundry. `await` is what hands the note to someone who'll do it.

#### 2 — `await` in a row is still a queue

```
elapsed: 1.51s   (0.4 + 0.6 + 0.5 = 1.5)
```

Every function is `async`. Every call is `await`ed. And it took exactly as long as doing them one at a time.

> **This is the single most common async mistake.** Marking things `async` buys you nothing on its own. You loaded the washing machine and stood watching it, three times.

#### 3 — `gather()` is where the win is

```
elapsed: 0.62s   (the SLOWEST one — not the sum)
```

Total time is now the longest single wait. You started all three machines, then waited once. Results come back in the order you *asked* for, not the order they finished — which is why unpacking `a, b, c` is safe.

#### 4 — One blocking call freezes everything

```
three polite_waiter (asyncio.sleep) : 0.51s
three rude_waiter   (time.sleep)    : 1.50s
```

**Identical code. Identical `gather()`. Identical durations. One is 3× slower**, and nothing about the shape of the program says why.

`asyncio.sleep` says *"I'm waiting — somebody else go."* `time.sleep` says nothing and holds the hands.

> **The rule:** inside `async def`, every waiting call must be an async one. One ordinary blocking call anywhere — `requests.get`, `time.sleep`, a heavy file read — silently converts your concurrent program back into a sequential one. Nothing crashes. It just gets slow, and the reason is invisible unless you know to look.

This is the experiment that makes the event loop *visible*. If only one thing from this chapter sticks, make it this one.

#### 5 — async is not threads, and does not help CPU work

```
two counts, awaited in sequence : 0.35s
two counts, gathered            : 0.37s
```

Barely any difference, and `gather()` is *slightly slower*. This is folding clothes: no machine running in the background, the work needs your hands throughout. `gather()` can only interleave at `await` points, and pure computation has none.

#### 6 — Why async spreads

To `await` something you must be inside `async def`. So the moment one function deep in your stack goes async, every caller must too — all the way up, until someone calls `asyncio.run()`. People call this **function colouring**, and it's the real cost of async.

```python
result = await Runner.run(agent, message)   # the SDK is async
result = Runner.run_sync(agent, message)    # the escape hatch
```

`run_sync` starts a loop, runs the coroutine, hands you the result. Use it while learning; reach for the async version when you want two agents running at once.

### ▶ Practice 5 — make the slow thing fast (30 min)

Write `slow_report.py`: three `async def` functions that each `await asyncio.sleep(1)` and return a string.

1. Call all three with `await` in sequence. Time it. Predict first.
2. Convert to `asyncio.gather`. Time it. Predict first.
3. Now change **one** of them to use `time.sleep(1)` instead. Predict the new total before running.
4. Try to call one of them from an ordinary `def`. Read the error.

**You're done when:** you predicted all three timings correctly, and can explain step 3's number to someone else without looking.

### ⚡ Challenge 5b — the leaky abstraction `[depth]` · 20 min

`asyncio.gather` runs everything. What happens when one of them raises?

Make one check raise a `ValueError`. Observe what `gather` does with the others. Then look up `return_exceptions=True` and decide which behaviour you'd want in an agent that's calling five tools at once — and why.

> **📍 Where you'll meet this:** `01_agent_loop/PROJECT.md` hands you `await Runner.run(...)`. All of Chapter 3 is async. And the SDK runs parallel tool calls with `gather` internally — which is why an SDK turn count differs from a hand-rolled loop's.

---

## 6. Writing one test `[core]` · 30 min

Chapter 2 ships 46 tests and asks you to add three attacks. That exercise only works if you've written an `assert` in a test file before.

> ### 🧠 The whole thing, in three facts
>
> 1. pytest collects files named `test_*.py` and functions named `test_*`.
> 2. A test **passes if it finishes**. It fails if an `assert` is False or it raises.
> 3. That is genuinely all. There is no framework to learn first.

```python
def test_a_taken_domain_is_unavailable():
    result = asyncio.run(domain("stripe"))
    assert result.available is False

def test_bad_names_are_rejected():
    with pytest.raises(ValidationError):
        NameRequest(name="My App")
```

### Testing async code without a plugin

`pytest` can't await a coroutine on its own. There are plugins that teach it how — **you don't need one.** The test is an ordinary function, and it can call `asyncio.run()` exactly like `__main__` does. One less dependency, and it keeps `asyncio.run` visible.

### `parametrize` — five tests from one function

```python
@pytest.mark.parametrize("bad_name", ["a", "My App", "hello!", "x" * 31, ""])
def test_bad_names_are_rejected(bad_name: str) -> None:
    with pytest.raises(ValidationError):
        NameRequest(name=bad_name)
```

pytest tells you *which* parameter failed, so a list of cases stays as debuggable as five separate tests.

### ▶ Practice 6 — write four (25 min)

```powershell
uv run pytest 00_python_for_agents/ -v
```

Read `solutions/test_namecheck.py`, then add four of your own. One must use `pytest.raises`, one must use `parametrize`, and one must test async code.

Then **make one fail on purpose** and read the output properly — pytest shows you the actual and expected values, and learning to read that is the skill.

**You're done when:** your four pass, and you've seen a real failure report.

> **📍 Where you'll meet this:** `02_typed_tools/solutions/test_expense_tools.py` — 46 tests, no API key, ~2 seconds. The first test suite in the curriculum, and you'll be asked to extend it.

---

## ✅ Checkpoint

Without looking:

1. What does `cast()` change at runtime?
2. Rewrite `@shout` above `def greet()` without using `@`.
3. Why does `field(default_factory=list)` exist?
4. `M(x=True).x` where `x: int` — what do you get, and why?
5. Three `await`s in a row, each 1s. Total time? Now with `gather`?
6. One of them uses `time.sleep`. Now what?
7. What makes pytest consider a test passed?

<details>
<summary>Answers to the opening diagnostic</summary>

1. pyright errors: `"upper" is not a known attribute of "None"`. **It's right** — `first([])` returns `None`.
2. `def greet(): return "hi"` then `greet = shout(greet)`.
3. Mutable default — one list shared by every instance. Needs `field(default_factory=list)`.
4. `1`. `bool` subclasses `int`, so `True` passes an `int` check and coerces.
5. `<coroutine object f at 0x...>` — calling an async function creates a job, it doesn't run one.
6. `assert 4 == 5` fails; pytest prints the comparison and exits **1**.

</details>

---

## Where to go now

| Order | File | What it is |
|---|---|---|
| 1 | [`PROJECT.md`](PROJECT.md) | **Name Check** — all six concepts in one small program |
| 2 | `solutions/` | Reference build. **Open after you attempt** |
| 3 | `../01_agent_loop/README.md` | Chapter 1 |

**You do not need to be fluent in these six things.** You need to have met them, so that when Chapter 1's first file uses four of them on one screen, none of them is the thing stopping you.
