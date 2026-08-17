# Agentic AI From Scratch

A hands-on curriculum that makes a student **fluent in the OpenAI Agents SDK** — by spiking each mechanism by hand just deeply enough that the framework stops feeling like magic, then building for real with the SDK.

This is not a personal experiment — it is a **teaching resource**. Instructors and students use this repository to learn, teach, and practice agentic AI. Every session must produce working code AND tasks that make students build something themselves.

> **The name is historical, and the scope is deliberate.** "From scratch" describes a *teaching device*, not the deliverable. We hand-roll what a student must be able to picture while debugging at 2am. Everything else is SDK from first contact.

---

## Who This Is For

| Audience | How they use this repo |
|----------|----------------------|
| **Instructors** | Teach each chapter over 2–3 sessions, use the drills as lab work, grade the project against its golden dataset |
| **Students** | Follow the build, do every inline practice, ship the three tracks (drill / spine / own agent) |
| **Self-learners** | Work chapters in order, treat the "You're done when..." criteria as mandatory gates |

### Prerequisites — stated honestly

Students need **working Python**, not beginner Python: functions, dicts, loops, exceptions, classes, imports, and comfort reading a traceback.

The following are **taught in Chapter 0**, not assumed: type hints that do work (`list[X]`, `X | None`, `Callable`, `cast`), decorators, dataclasses, Pydantic, `async`/`await`, and writing a pytest test. A student who skips Chapter 0 will stall in Chapter 2.

**Chapter 0's scope rule, applied when it was built:** a concept earns a place only if it appears in Ch1–3 *without being taught in place* **and** a student who doesn't know it is stuck rather than merely slower. That is why `Literal` and `Annotated` are **not** in Chapter 0 — Ch2 §5 and §6 teach them properly, in the context where they earn their keep, and duplicating that would strip them of their motivation. Apply the same test before adding anything.

No AI/ML background is needed. `PYTHON_ROADMAP.md` is the deeper self-study track for anyone who finds Chapter 0 hard.

**Rule: never describe the prerequisite as "basic Python" anywhere in this repo.** It was false, it cost students their confidence, and it is the single most damaging sentence a curriculum can ship.

---

## The Goal

A graduate should be able to say:

> *"I understand what an agent framework does internally, but I don't need to build everything myself. I can confidently use the OpenAI Agents SDK to design, build, evaluate, debug and extend real agentic applications."*

Concretely, they can:

1. Open a blank file and write a working, tool-using, evaluated SDK agent **unaided**
2. Explain what the SDK is doing underneath any abstraction they use
3. Debug an emergent agent failure — a dropped handoff, a context overflow, a guardrail fighting an old system prompt
4. Prove an agent works with a golden dataset and a regression suite

Note the order. #1 is the destination. #2 exists to serve #1.

---

## THE DEPTH POLICY — the law this curriculum is governed by

> **Hand-roll only what a student must be able to picture while debugging. Everything else is SDK from first contact.**

This exists because the repo previously failed the other way. Chapter 2's largest single time investment was rebuilding a decorator that generates Pydantic models from an empty file — 60–90 minutes of metaprogramming in a course about building agents. **The means ate the goal.** That must never happen again.

### The three depths — every concept gets exactly one

| Depth | What it means | Budget | Lives in |
|---|---|---|---|
| 🔨 **Spike** | Hand-rolled, ≤60 lines, demonstrates the mechanism, then **deleted or archived** — never maintained, never extended, never the thing the project runs on | ≤30 min | `spike/` |
| 📖 **Observe** | Shown and traced, not rebuilt. Read the SDK's behaviour, print what it produces, predict then verify | ≤15 min | `README.md` |
| 🚀 **SDK-native** | Never hand-rolled at all. Taught directly through the SDK, on the first contact | full chapter | `with_sdk/` |

### The assignment, as a standing decision

| Concept | Depth | Why |
|---|---|---|
| The agent loop (call → parse → execute → feed back) | 🔨 Spike | The single most load-bearing mental model in the field |
| Tool-call JSON — the request and the result message shape | 🔨 Spike | Every tool bug is read at this layer |
| Message-array growth across turns | 🔨 Spike | Prerequisite for understanding sessions, context and cost |
| One hand-written schema **dict** | 🔨 Spike | Students must see what a tool looks like to a model |
| A schema **generator** (`inspect` → `create_model`) | ❌ **Cut** | Metaprogramming. Not agent building. `@function_tool` does it |
| Validation failure — one bad payload, one raised error | 🔨 Spike | The trust boundary, felt once |
| Structured outputs | 📖 Observe | Trace the JSON schema the SDK emits; don't rebuild the parser |
| Context-window trimming | 🔨 Spike | Students must feel an overflow to respect it |
| Sessions & persistence | 🚀 SDK-native | `SQLiteSession` — nothing gained by rebuilding a table |
| Context objects / dependency injection | 🚀 SDK-native | `RunContextWrapper` is plain Python DI; no mystery to dispel |
| Handoffs, agents-as-tools | 🚀 SDK-native | Emergent behaviour is the lesson, not the plumbing |
| Guardrails & approvals | 🚀 SDK-native | The judgement is the lesson, not the tripwire mechanics |
| Tracing, streaming, cost accounting | 🚀 SDK-native | Reimplementing a tracer teaches nothing about agents |
| Evals / golden datasets | 🔨 Spike **then** 🚀 | Hand-built in Ch1 as a habit; formalised in Ch6 |

**Before adding any hand-rolled section to any chapter, answer in writing in the chapter README:** *what will the student be unable to debug if we skip this?* No answer, no spike.

---

## THE THREE TRACKS — every chapter ships all three

The old curriculum ran ~40 tasks across two domains (arithmetic and expenses). That produces students who learned how *Spendly* does memory, not how memory works. Transfer requires varied surface context, and autonomy requires a project nobody specified for them.

| Track | What | Domain | Graded on |
|---|---|---|---|
| 1️⃣ **Drills** | Small, isolated, **disposable** SDK reps. 10–20 min each | **Rotating throwaway domains** — dice, timers, fake weather, unit converters, trivia. **Never expenses** | Does it run |
| 2️⃣ **The Spine** | Spendly Lite. Locked spec, locked seed data, locked golden dataset | Expenses, always | The golden dataset — **plus every prior chapter's cases still passing** |
| 3️⃣ **Your Own Agent** | Self-chosen domain, **picked in Chapter 1**, extended every chapter after. SDK-only, blank file, no scaffolding | Whatever the student chose | **Evidence, not functionality** — 3 logged runs + what broke + what you changed |

### Track 3 is the whole recommendation

It fixes transfer, autonomy, portfolio differentiation and honest assessment in one move, and it costs near-zero design time because **the rubric is identical in every chapter**:

```
Your Own Agent — Chapter N increment
  [ ] The chapter's capability is present and working in YOUR agent
  [ ] RUNS.md has 3 new runs, dated, with actual output pasted in
  [ ] One paragraph: what broke, and what you changed
  [ ] It is not an expense tracker
```

That block is copy-pasted verbatim into every chapter. Never grade Track 3 on features — grade it on evidence. A student whose agent broke and who documented why has met the bar; a student with a working agent and no runs has not.

**Drills must be at least half SDK-native from Chapter 3 onward.** A student who has only ever *modified* SDK code cannot write it. Recognition, recall and generation are three different competencies — the old curriculum tested only the first.

---

## THE TAPER RULE — build-twice is O(n²) and has an expiry date

Building the project twice — once by hand, once on the SDK — earns its keep early. In Chapter 1 it is genuinely clever: the second implementation doubles as a second behavioural sample of a non-deterministic system, graded by one dataset.

But the app grows, and the doubling applies to the *whole app*. Left alone this collapses around Chapter 5–6 as fatigue. So it is written down now, as design:

| Chapters | The spine (Spendly Lite) | The hand-rolled layer |
|---|---|---|
| **1–2** | Built twice — scratch **and** SDK, one golden dataset grades both | A real, maintained implementation |
| **3+** | **SDK-only.** One codebase, one implementation | A throwaway spike — 40–60 lines, demonstrates the mechanism, **deleted after the chapter** |

> **Amended at Chapter 3** (the rule originally said "1–3 both builds"). Chapter 3's hand-rolled mechanism is prompt-and-parse, and §3 of that chapter spends twenty-five minutes proving it cannot be made correct. Building the spine on top of it to preserve a symmetry would have meant shipping a practice the chapter had just disproved.
>
> Generalise the correction, because it will come up again: **build-twice is worth it when the hand-rolled version is correct-but-verbose, and worth nothing when it is simply worse.** Chapters 1 and 2 were the first kind. Everything after is the second.

`spike/` files are explicitly not maintained. They are not imported by the project, not covered by the golden dataset, and may be deleted the moment the chapter validates. Mark them with a header docstring saying exactly that.

---

## TIME BUDGETS — state them honestly or don't state them

Old headers claimed ~4 hrs for Chapter 1 and implied a 90-minute session. Adding the file's own per-task numbers gives 9–11 hrs for Chapter 1 and 15–20 for Chapter 2. **That is an honesty problem, not a pedagogy problem**, and it is the most likely cause of real-world failure: instructors abandon the session plan in week one, and on-pace students conclude they are slow.

Rules:

1. **Every chapter header carries two numbers: Core and Full.** Core = the critical path a student must finish to start the next chapter. Full = core + every depth section, challenge and optional drill.
2. **Every task keeps its own minute estimate, and the header must equal their sum.** If the arithmetic disagrees with the header, the header is wrong.
3. **Every section is marked `[core]` or `[depth]`.** A student on the core path can skip every `[depth]` block and still pass the next chapter's prerequisites. This is what makes an honest budget actionable instead of merely discouraging.
4. **A chapter is 2–3 sessions, not one.** Stop advertising 90 minutes.

---

## The Roadmap — provisional beyond the next chapter, by design

Chapters are specified **only after the previous one is built and validated**. This is why Ch1 and Ch2 cohere. Treat everything below the line as a hypothesis, not a commitment — and keep exactly one roadmap in the repo. (Three contradictory ones shipped simultaneously once. Root `README.md` and `SDK_BRIDGE.md` mirror this table; when it changes, they change.)

| Ch | What You Build | Depth signature | Axes | Status |
|----|---------------|---|------|--------|
| 0 | **Python for Agents** — typing, decorators, dataclasses, Pydantic, async, pytest | prerequisite bridge | — | ✅ Built |
| 1 | **The Agent Loop** | 🔨 spike-heavy, by design | 🧠🔒📐 | ✅ Built + retrofitted |
| 2 | **Typed Tools** | 🔨 one spike, then SDK | 🔒📐 | ✅ Built + retrofitted |
| 3 | **Structured Outputs** | 🔨 failing spike → 🚀 | 📐🧠 | ✅ Built |
| — | *below this line is hypothesis* | | | |
| 4 | **Sessions & State** — the next to specify | 🚀 | 🧠 | ⬜ Next |
| 5 | **The Context Window** — Ch4's failure mode | 🔨 → 🚀 | 🧠 | ⬜ |
| 6 | **Evals** — golden datasets, LLM-as-judge, regression | 🚀 | 📐 | ⬜ |
| 7 | **Specialists** — handoffs, agents-as-tools | 🚀 | 🧠🔒 | ⬜ |
| 8 | **Guardrails & Approvals** | 🚀 | 🔒 | ⬜ |
| 9 | **Observability** — tracing, streaming, cost & token accounting | 🚀 | 📐 | ⬜ |
| 10 | **Serving & MCP** — FastAPI + Model Context Protocol | 🚀 | 🔒📐 | ⬜ |
| 11 | **Hosted Tools & the Responses API** — the one paid chapter (~$5) | 🚀 | 🔒 | ⬜ |
| 12 | **Cold Build Capstone** — unfamiliar domain, no scaffolding | 🚀 | all | ⬜ |

### Two structural decisions encoded above

**Evals sit in the middle (Ch6), not at the end.** From Ch6 onward, *"the Ch6 suite is still green"* is an acceptance criterion for **every** later chapter. That one rule converts a growing project into a compounding one, and teaches regression pressure — which is the actual daily experience of maintaining an agent.

**Ch12 is the only honest assessment instrument in the curriculum.** A cold build in an unfamiliar domain with no scaffolding is the only thing that distinguishes *"learned it"* from *"copied it."* Without it there is no such instrument at all.

### The paid chapter is deliberately last

Every chapter but the last runs **free** on Gemini's OpenAI-compatible endpoint, which speaks **Chat Completions**. The Agents SDK defaults to the **Responses API**. That is a real difference and we do not hide it — see `RESPONSES_VS_CHATCOMPLETIONS.md`.

The choice is not a compromise; the state chapters *require* it. You cannot teach context-window management when the server owns the transcript behind a `previous_response_id` — there would be nothing in the student's process to prune. Client-side state is a prerequisite, not a limitation.

What Chat Completions genuinely cannot do is **hosted tools** — `WebSearchTool`, `FileSearchTool`, `CodeInterpreterTool`, `ComputerTool`, `HostedMCPTool`. Those run on OpenAI's servers and exist in the API, not the SDK. Students meet them last, *after* having hand-rolled the equivalents, so the comparison lands. Budget ~$5 of OpenAI credit; one environment variable switches the whole curriculum over:

```
AGENT_PROVIDER=openai   # in .env — see shared/models.py
```

**Rule:** no chapter before the hosted-tools chapter may require a paid key. If a concept cannot be taught free, it moves there or gets spiked.

---

## Stack

| Choice | Why |
|--------|-----|
| **Python 3.12+** | Type hints, modern stdlib |
| **`uv`** | Fast, modern Python package manager — replaces pip + venv |
| **`openai-agents`** | **The destination.** The SDK students are here to master |
| **`openai` SDK** | Transport layer for spikes, against any OpenAI-compatible endpoint — including Gemini's `/v1beta/openai/` |
| **`python-dotenv`** | Keep API keys out of source |
| **`pydantic`** | The validation layer. From Chapter 2 on, tool contracts are Pydantic models — the same choice FastAPI and the Agents SDK made |
| **`ruff`** | Formatter + linter in one binary. Replaces black, isort, flake8 and pylint |
| **`pyright`** | Static type checker — catches bugs before runtime |
| **`pytest`** | The proof layer. Boundary tests run with no API key, in milliseconds |
| **No *other* agent framework** | No LangChain, LlamaIndex, Haystack, CrewAI — anywhere |

We use **Gemini free models via the OpenAI-compatible endpoint** so cost is zero while learning.

---

## Setup

### Prerequisites

- Python 3.12 or higher
- [uv](https://docs.astral.sh/uv/getting-started/installation/) installed (`pip install uv` or see docs for platform-specific install)
- A free Gemini API key from https://aistudio.google.com/apikey

### Installation

```powershell
cd C:\Users\Faraz\Desktop\agentic-ai-from-scratch
uv sync
copy .env.example .env
# Open .env and paste your Gemini API key
```

`uv sync` reads `pyproject.toml`, creates the `.venv`, and installs all dependencies in one step.

### Run Chapter 1

```powershell
uv run python 01_agent_loop/from_scratch/agent.py
```

---

## The Quality Gate — non-negotiable, every chapter

This repository holds the same bar a production Python repo holds. A teaching repo has no excuse for a lower one: students copy what they see, and code quality tooling is not a topic to be covered later — it is the environment the work happens in.

Four commands, in this order, cheapest first:

```powershell
uv run ruff format .     # style   — automatic, never argued about
uv run ruff check .      # lint    — bugs a linter sees without running code
uv run pyright           # types   — bugs a linter cannot see
uv run pytest            # proof   — bugs nothing sees without running the code
```

**Target: all four clean.** 0 ruff findings, 0 pyright errors, 0 pyright warnings, green pytest.

| Tool | What it owns | Configured in |
|---|---|---|
| `ruff format` | Formatting. `*.md` excluded — chapter prose contains deliberately wrong code | `[tool.ruff.format]` |
| `ruff check` | `E W F I UP B C4 SIM RUF`. `E501` off (the formatter owns line length) | `[tool.ruff.lint]` |
| `pyright` | `standard` mode. One `executionEnvironments` block **per script-style folder** | `[tool.pyright]` |
| `pytest` | Collects `test_*.py` only. `check_*.py` harnesses cost real API calls and are run deliberately | `[tool.pytest.ini_options]` |

### Two configuration facts that will bite whoever adds the next chapter

1. **Every chapter has its own `tools.py`** and scripts import it by bare name. A flat `extraPaths` puts them all on one search path and resolves them to whichever came first. Each script-style folder therefore gets its own `[[tool.pyright.executionEnvironments]]` block. **Add one when you add a chapter** — `spike/` folders included. Same reason `[tool.ruff] src` lists them.
2. **`check_*.py` must never be collected by pytest.** They are golden-dataset harnesses — real API calls, minutes of runtime, rate-limit pauses. `python_files = ["test_*.py"]` keeps `uv run pytest` free and fast.

### Where a test belongs

| Question | Where | Cost |
|---|---|---|
| Is a bad argument rejected? Does the enum reach the schema? | `test_*.py` | free, milliseconds |
| Did the agent ask instead of guessing? Did it recover? | `check_*.py` | real calls, minutes |

Push every assertion down to the cheap layer. Spend model calls only on what genuinely needs a model.

---

## The Framework Rule (scoped, not absolute)

**Mastering the OpenAI Agents SDK is the goal. Hand-rolling is how we make the SDK legible — it is the means, not the destination.**

| Folder | Rule |
|---|---|
| `spike/` (Ch4+) and `from_scratch/` (Ch1–3) | **No agent framework.** No `from agents import ...`. The OpenAI SDK is a transport layer only. Subject to the depth policy — a spike that exceeds 60 lines is a design failure, not a thorough lesson |
| `with_sdk/` | **No hand-rolling.** Use the OpenAI Agents SDK as intended. Re-implementing what the SDK provides defeats the purpose of this layer |

If a framework solves it in 3 lines, we write the 30 lines underneath so we know what those 3 lines *cost* — **and then we use the 3 lines, forever after.**

A student finishing a chapter must be able to say: *"I built this mechanism, I know what the SDK does instead, I can name what it does for me — and I just used the SDK to build something of my own with it."*

## The Three Axes (tag every chapter)

Agent Factory's framing — *"every agent bug is either a state bug or a trust bug"* — extended with the axis that matters most for this curriculum's weakest area:

| Axis | Question | Examples |
|---|---|---|
| 🧠 **State** | What does it remember? | the message list, context window, sessions, compaction |
| 🔒 **Trust** | What is it allowed to do? | tools as permissions, `max_turns`, guardrails, approval gates |
| 📐 **Proof** | How do we know it worked? | golden datasets, run evidence, traces, evals |

Tag each chapter and each concept. Make *"is this a state bug, a trust bug, or a proof gap?"* the standing debrief question.

---

## Curriculum Design Principles

### THE NON-NEGOTIABLE RULE — Practice Follows Every Concept

> **Reading is not learning. A student who only reads or watches forgets the concept before the next chapter and arrives at it unable to build.**

Therefore, in this repository, **no concept is ever taught without a hands-on task attached to it.** This is not a nice-to-have and it is not deferred to the end of the chapter.

```
CONCEPT  ->  PRACTICE  ->  (CHALLENGE)  ->  ... repeat per section ...  ->  CHAPTER PROJECT
```

| # | Element | Rule |
|---|---------|------|
| 1 | **Teach the concept** | Mental model / analogy first, then the code |
| 2 | **Practice immediately** | A small hands-on task **inside the README, directly under the concept it teaches**. Never batched at the end. 5–15 minutes |
| 3 | **Challenge where it fits** | A short "push further" task. Optional per section; several per chapter |
| 4 | **Chapter project** | Combines every concept in the chapter into one working thing. Mandatory |

**Difficulty must climb** — read → edit → extend → **design from a blank file**. That last rung is the one the old curriculum was missing: *every chapter must contain at least one task that starts from an empty file with no scaffolding.* Track 3 satisfies it by default.

**Never write a chapter as pure prose.** If a section explains something and does not ask the student to do something, the section is unfinished.

### The Six Layers — every chapter has all of them

| Layer | Where | What |
|---|---|---|
| 1 **Concept** | `README.md` | The mechanism, taught plainly, mental model first |
| 2 **Spike** | `spike/` (or `from_scratch/`, Ch1–3) | The mechanism by hand — **only where the depth policy says so** |
| 3 **Practice** | inline + `EXERCISES.md` | Drills (Track 1) — rotating domains, half SDK-native from Ch3 |
| 4 **SDK** | `with_sdk/` | The capability on the OpenAI Agents SDK, plus `compare.md` |
| 5 **Bridge** | `../SDK_BRIDGE.md` | Our code → SDK abstraction → what it does for us |
| 6 **Project** | `PROJECT.md` | Track 2 (spine) **and** Track 3 (own agent) increments |

**Layer 4 is the destination, and Layer 2 is optional.** A chapter that stops at the hand-rolled version has failed its purpose. A chapter with no hand-rolled layer at all is perfectly valid — most later chapters should have none.

```
chapter_folder/
  README.md       # [core]/[depth] marked. Concept -> inline Practice -> ...
  spike/          # hand-rolled mechanism, <=60 lines, disposable (omit if none)
  with_sdk/       # the real implementation + compare.md
  EXERCISES.md    # Track 1 drills: warm-up -> guided build -> blank-file challenge
  PROJECT.md      # Track 2 spine increment + Track 3 own-agent block + rubric + Spendly Transfer
  solutions/      # Reference solutions (grading + self-check AFTER attempting)
```

### The spine is ONE project

**Spendly Lite** — a personal expense assistant — is built in Chapter 1 and extended in every chapter after. Locked spec, locked seed data, locked golden dataset: **determinism is what makes it gradeable**, so do not "improve" the spec chapter to chapter.

It deliberately mirrors the architecture of Spendly, Faraz's real WhatsApp expense product (intent → specialists → structured outputs → SQLite), but it is a clean-room teaching build: **no external services, no API keys beyond the model, no business-sensitive material.**

**The regression rule:** every prior chapter's golden-dataset cases must still pass. A chapter that breaks Chapter 2's cases is not done.

### 🔁 Spendly Transfer

Every chapter ends with a short, concrete task porting the chapter's concept into the **real** Spendly codebase (`C:\Users\Faraz\Desktop\Spendly\`). This satisfies the standing rule that Spendly is the spine, without coupling the curriculum to the product.

### Exercise tiers (Track 1)

1. **Warm-up** — modify existing code. Proves the student can read and edit.
2. **Guided build** — apply the concepts to build something new, with acceptance criteria.
3. **Blank-file challenge** — open an empty file and produce a working SDK agent unaided. **Mandatory from Chapter 3 on.**

Drills rotate domains deliberately — dice, timers, fake weather, trivia — and **never** use expenses. That is the spine's job.

### Acceptance criteria are explicit

Every practice task, exercise and project ends with **"You're done when..."** followed by concrete, checkable conditions. No fuzzy milestones.

### Every chapter project must produce evidence

Both project tracks require `RUNS.md` — real runs, dated, with actual output. Track 2 grades against the golden dataset; Track 3 grades on evidence alone. This starts the eval habit at Chapter 1 so that by Chapter 6 it is muscle memory rather than framework magic.

### Pedagogy that is working — do not touch

These were validated in Ch1 and Ch2 and every later chapter should copy them:

- **Prediction + confidence rating + `<details>` gated spoilers** before revealing any answer
- **Bug-first sequencing** — `break_it.py` before the fix. A found bug is worth more than an invented example
- **Real defects documented in place** — Ch2 §7b's failure narrative is the best page in the repo
- **Chapter-to-chapter hooks** — Ch2 opens by re-reading a line of Ch1's own code as a security question. Every chapter should open by re-reading the previous chapter's code as a new kind of question

---

## Session Delivery Guide (for Instructors)

**A chapter is 2–3 sessions of 90–120 minutes, not one.** Check the chapter header's Core/Full budget before planning.

| Phase | Duration | Activity |
|-------|----------|----------|
| **Concept + inline practice** | 40–50 min | Teach one concept, students immediately do the task under it, repeat. Never more than ~8 min of talking before they type something |
| **Drills** | 30–40 min | Track 1. Rotating domain, instructor circulates |
| **Debrief** | 10–15 min | Review. Discuss what broke. Name the limitation this chapter cannot solve — that is the hook for the next one |
| **Project** | Lab / homework | Track 2 spine increment + Track 3 own-agent increment, both with `RUNS.md` |

### Key teaching moves

- **Don't show the code first.** Start with the mental model. Ask students to predict.
- **Run before reading.** Let them see the output, then trace backward.
- **Let exercises fail.** Students hitting real bugs is the learning. Don't preempt it.
- **Skip the `[depth]` blocks in class.** They are for students who want them, not for the session plan.
- **Connect forward.** End every session by naming what the current chapter can't do.

---

## Chapter Completion State

### Chapter 0 — `00_python_for_agents/` ✅ built

The prerequisite bridge. Six sections, ≈6 hrs core. No SDK layer and no Spendly increment — nothing agentic happens here, so Layers 4 and 5 do not apply. Every section ends with a **📍 where you'll meet this** box naming the exact file and line in Ch1–3.

- Opens with a **6-question diagnostic**, one per section, so a strong student skips the chapter in ten minutes instead of skipping the two sections they actually needed
- `examples/foundations.py` — `list[X]`, `X | None` narrowing, `Callable` registries, `cast()`, dataclasses with `default_factory` and `@property`
- `examples/decorator_lab.py` — proves `@x` is literally `f = x(f)`; a timing decorator; **the `functools.wraps` bug** (a wrapper that eats the docstring produces a tool the model cannot understand, and nothing crashes); and the registry decorator that is 80% of Ch2's `@tool`
- `examples/pydantic_lab.py` — multi-error reports, and the **bool-is-an-int trap** presented as the real bug this repo shipped
- `examples/async_lab.py` — **the centrepiece.** Six experiments with measured timings
- `solutions/namecheck.py` + `test_namecheck.py` — the project

**Async is 75 of the chapter's 270 minutes**, because it is the concept most often skipped and the one that then breaks everything downstream. The model is **one person, several machines** (laundry — deliberately not a kitchen, so it does not collide with Ch1's restaurant). The six experiments each kill one misconception, and the timings are real:

| # | Kills | Measured |
|---|---|---|
| 1 | "I called it, so it ran" | returns a coroutine object |
| 2 | **"I made it async, so it's fast"** | 3 sequential awaits = **1.51s** |
| 3 | — | same 3 gathered = **0.62s** |
| 4 | **the invisible one** | `asyncio.sleep` **0.51s** vs `time.sleep` **1.50s**, identical code |
| 5 | "async makes CPU work parallel" | 0.35s vs 0.37s — gather is *slower* |
| 6 | "why is async everywhere" | function colouring, and `run_sync` |

Experiment 4 is the one to teach hardest — it is the only one that makes the event loop visible, and the failure it describes is silent in production.

**The project is `namecheck.py`** — "is this startup name available?", checking domain/handle/trademark concurrently. Chosen because the three questions are genuinely independent, so concurrency is motivated rather than decorative, and because its structure *is* Chapter 1's: a registry, dispatch by name, a typed report. The only thing Chapter 1 adds is that a model picks the entries. `--slow` runs the same checks sequentially: 1.50s vs 0.60s.

Two type-level decisions are documented in the code because both are things a student will hit and mis-fix: `CheckFn` uses `Coroutine` rather than `Awaitable` (`asyncio.run` requires a coroutine, and pyright is right to object), and `REGISTRY` in `foundations.py` uses `Callable[..., float]` rather than a precise signature (a named-parameter call cannot be checked against a positional `Callable`, and Ch2 buys that checking back at the boundary).

### Chapter 1 — `01_agent_loop/` ✅ built + retrofitted

- `from_scratch/agent.py` + `tools.py` — the five-step loop with `MAX_ITERATIONS`, error handling, typed
- `with_sdk/agent_sdk.py` + `compare.md` — the same agent on `Agent`/`Runner`/`@function_tool`, plus the line-by-line map
- `README.md` — kitchen analogy, 9 concepts each with an inline practice, prediction + confidence + `<details>` spoilers, 2 checkpoints, axis tags
- `EXERCISES.md` — 3 warm-ups, 2 guided builds, 2 challenges, all with acceptance criteria
- `PROJECT.md` — **Spendly Lite v1**, built twice and graded by one 5-case golden dataset; includes the Spendly Transfer
- `solutions/` — `loop.py` (retries 429s), unit-converter agent, `expense_*` builds, `check_expenses.py`
- Gate clean; both builds verified against the dataset

**Retrofit done:** honest budget table (core ≈7 hrs / full ≈10–11, replacing the "~4 hrs" claim); **Track 3 kickoff** — students pick their own agent's domain in the README's setup section and build v1 in `PROJECT.md`; the `await Runner.run(...)` async gap now carries an inline explainer pointing at Chapter 0 and mentioning `Runner.run_sync`; a note that Ch1 hand-rolls more than any later chapter *on purpose*; dead comment block at `from_scratch/agent.py:85-88` deleted.

All nine concepts are marked `[core]` with per-concept estimates — **correctly**, because a foundation chapter has no skippable loop. A note at the top says so explicitly, so the marking doesn't read as laziness. Chapter 1's depth lives in `EXERCISES.md` (Exercises 1–3 core, 4–7 `[depth]`) and in the project's second build. Budget: core ≈8 hrs, full ≈11.5.

### Chapter 2 — `02_typed_tools/` ✅ built + retrofitted

Chapter 1 asked *"can the model call my function?"*; Chapter 2 asks *"what happens when it calls it wrongly?"*

- `from_scratch/break_it.py` — six hostile payloads through Ch1's dispatch. **Two do not raise**: `add(a="5", b="3") -> "53"`, and an invalid category written to storage
- `from_scratch/handrolled.py` — ~85 lines of `isinstance` gauntlet for ONE tool
- `from_scratch/typed_tool.py` — `@tool`: `inspect.signature` → `create_model` → `model_json_schema`. Plus `ToolError`, `explain()`, `_clean_schema()`
- `from_scratch/tools.py`, `agent.py` — the calculator agent with `Literal`, `Annotated`, `MAX_INVALID_CALLS`
- `with_sdk/agent_sdk.py` + `compare.md` — `@function_tool`, and `failure_error_function` for overriding the SDK's privacy-driven error default
- `README.md` — 10 concepts, each with an inline practice, 2 challenges, 2 checkpoints
- `EXERCISES.md` — 3 warm-ups, 2 guided builds, 2 challenges
- `PROJECT.md` — **Spendly Lite v2**, built twice, graded by one 7-case dataset
- `solutions/test_expense_tools.py` — the first test suite in the curriculum: 46 tests, no API key, ~2 seconds
- Gate clean; both builds pass 34/34 golden-dataset checks

**Retrofit done** — this is the chapter the depth policy was written for:

- **Budget table** with a per-part breakdown: core ≈11 hrs, full ≈18–20. Every section marked `[core]` or `[depth]` with its own estimate; the header is the sum
- **§4 split.** Core now *uses* `@tool` and understands the one-declaration-three-outputs idea; the `inspect`/`create_model`/`get_type_hints` internals moved to **§4b `[depth]`**
- **Guided Build 1 → Guided Build B `[depth]`**, with an explicit note that it used to be mandatory, that cutting it was deliberate, and not to do it because Chapter 3 needs it (it doesn't). The content is untouched — nothing was deleted, only re-tiered
- **§10 is now the longest section**, opening with "from here on `@function_tool` is how you define a tool"
- **New §11** — every chapter idea in SDK vocabulary, including `name_override` and `is_enabled` which we never built
- **New Practice 12 `[core]`, mandatory** — a dice/probability agent from a genuinely empty file. This is the chapter's first generation task; everything before it was recognition or modification
- **New Warm-up 4** — `split_bill` written twice, `@tool` then `@function_tool`, ending on "if the annotations transfer unchanged, what did writing `@tool` first actually teach you?"
- **New Guided Build A `[core]`** — a library-catalogue tool suite, SDK-only, unfamiliar domain
- **Track 3 block** added to `PROJECT.md`; **the regression rule** (Chapter 1's five cases must still pass) added to the acceptance checklist

**Three real defects found while building this chapter**, all documented in place. Use them in class:

1. `amount: true` accepted as `1.0` (bool subclasses int). Found by `pytest` on its first run. Fixed with a `BeforeValidator`.
2. That fix silently degraded the schema: with a custom validator attached, Pydantic emits raw `"gt": 0` instead of `exclusiveMinimum`, which is not a JSON Schema keyword, so the model stopped being told. Nothing crashed. Fixed by `_clean_schema()`; guarded by a test.
3. **The one that matters most.** The system prompt's "never correct the user's value yourself" rules were deleted on the grounds that `Literal` and `Field(gt=0)` now enforce them. The golden dataset then failed three cases: given `-450`, the model flipped the sign *before* calling and logged a fabricated `450`. The type worked perfectly — it just never saw a negative number. **A type stops a bad value from being accepted; it does not stop the model from manufacturing a good one.** Rules restored, failure recorded above them in `expense_agent.py`, taught as README §7b.

---

### Chapter 3 — `03_structured_outputs/` ✅ built

The first chapter designed under the depth policy, and the first SDK-only spine. Budget: core ≈9 hrs, full ≈14.5.

- `from_scratch/prompt_and_parse.py` — **a spike that fails on purpose.** Replays 8 real captured Gemini responses to an explicit "reply with JSON and nothing else" prompt: **3/8 survive `json.loads`**, 7/8 survive a regex-hardened parser, 6/8 survive validation. Runs offline and free; `--live N` reruns it against the model for a different distribution
- `with_sdk/agent_sdk.py` + `compare.md` — `output_type=`, and the union demo where "I need to ask" becomes a shape
- `solutions/replies.py` — **the chapter.** Four branches (`Logged`/`Reported`/`NeedMoreInfo`/`Refused`) whose members are exactly the outcome classes Chapter 2's dataset was already classifying by substring. Plus `exactly_one_branch`, the curriculum's first guardrail
- `solutions/expense_agent_v3.py` — SDK-only spine; imports Ch2's tools and storage unchanged, adds `output_type` and one prompt section. Re-adds the 429 backoff that was silently lost when Ch2 moved to `Runner.run`
- `solutions/check_expenses.py` — 9 cases, **zero substring assertions**. Ch2's seven converted (regression rule), plus precision-of-the-ask (`missing == ["category"]`) and refusal classification
- `solutions/test_replies.py` — 11 offline tests including `test_a_valid_shape_can_still_be_a_lie`, which passes on fabricated data on purpose
- `solutions/_bootstrap.py` — the runtime `sys.path` shim the "one continuous spine" decision costs. pyright's `extraPaths` does not run anything; the interpreter needs telling separately
- `README.md` — 10 sections, §10 the mandatory blank-file drill (support-ticket triage, unfamiliar domain)

**The chapter's argument for its own position:** structured outputs are not a feature, they are what makes evaluation possible. Ch2 made the input boundary testable and bought 46 unit tests; Ch3 makes the output testable and buys evals that mean something. That is why it lands before the evals chapter.

**§8 is the chapter's §7b** — the honest limitation, in the same shape as its predecessor. A type stops a bad value but not an invented one (Ch2); a schema stops a malformed answer but not a well-formed false one (Ch3). Same failure, better clothes, each chapter narrowing without closing it.

**Two real defects found while building the chapter.** Both are documented in place. Use them in class — a found bug beats an invented example:

1. **The one the chapter is about.** On the new dataset's first run, `subtract` returned **16000** and the agent told the user **14,500**. It had taken `month_total`'s post-write 9000 and subtracted the just-logged 1500 a *second* time. Every tool call was correct; only the summary was wrong. **This had been happening in Chapter 2 the whole time** — its assertion was `"16000" in answer`, so the failure showed up as one anonymous line among 34 and read as model noise. `reply.logged.remaining == 16000` named it immediately. Fixed by a `REPORTING NUMBERS` block in the system prompt, **not** by a type: the reply's shape was flawless and no schema could have objected. Taught as §1, revisited in §8. The lesson is the division of labour — *a type makes a failure impossible to express, a schema makes it impossible to hide, a cross-check makes it impossible to ship, and a prompt does none of the three.*
2. **A flaky harness is a broken harness.** At a 30-second inter-case pause the dataset poisoned itself: a 429 mid-case exhausted the SDK's internal retries, the run died with `MaxTurnsExceeded`, and all fifteen checks in that case failed for reasons unrelated to the agent — 25/58 on a suite that passes. Pause raised to 45s, backoff to 20s, and `check_expenses.py` now line-buffers stdout so a redirected 6-minute run is not indistinguishable from a hang. **If a dataset is flaky, fix the harness before touching the agent** — an eval that fails for infrastructure reasons teaches nothing and costs you trust in the suite.

---

## Development Commands

| Task | Command |
|------|---------|
| Install / sync dependencies | `uv sync` |
| **The gate** (run all four before calling anything done) | `uv run ruff format . ; uv run ruff check . ; uv run pyright ; uv run pytest` |
| Format | `uv run ruff format .` |
| Lint (auto-fix) | `uv run ruff check . --fix` |
| Type check everything | `uv run pyright` |
| Unit tests (free, offline, ~2s) | `uv run pytest` |
| Run a chapter | `uv run python 02_typed_tools/from_scratch/agent.py` |
| Run the SDK build | `uv run python 03_structured_outputs/with_sdk/agent_sdk.py` |
| Ch3 spike — 8 real responses, free and offline | `uv run python 03_structured_outputs/from_scratch/prompt_and_parse.py` |
| Ch3 spike — against the live model | `uv run python 03_structured_outputs/from_scratch/prompt_and_parse.py --live 6` |
| Run the spine (current version) | `uv run python 03_structured_outputs/solutions/expense_agent_v3.py` |
| Check which provider/model is wired (free, no tokens) | `uv run python -m shared.models` |
| Grade Ch2 (both builds) | `uv run python 02_typed_tools/solutions/check_expenses.py [--impl sdk]` |
| Grade Ch3 (9 cases, ~12 min — free tier is the bottleneck) | `uv run python 03_structured_outputs/solutions/check_expenses.py` |
| Add a dependency | `uv add <package>` |

---

## Project Files

| File | Purpose |
|------|---------|
| `shared/models.py` | **The model factory.** `make_model()` — the one seam between Chat Completions/Gemini and Responses/OpenAI. Every `with_sdk/` file uses it; no spike file may |
| `INSTRUCTOR.md` | **The teaching manual.** Prep loop, session shape, grading, gotchas. This file holds the *rules*; that one holds the *practice* |
| `SDK_BRIDGE.md` | Our code → SDK abstraction → what it does for us. Grows every chapter |
| `PYTHON_ROADMAP.md` | Deeper Python self-study. **Gitignored** — do not link it from public docs |
| `RESPONSES_VS_CHATCOMPLETIONS.md` | Why the curriculum runs on Chat Completions, what it costs, where the escape hatch is |
| `pyproject.toml` | Project metadata and dependencies. Has a `[build-system]` solely so `shared/` installs as an importable package |
| `uv.lock` | Locked dependency versions (commit this) |
| `.env.example` | Template for API keys — copy to `.env` and fill in |
| `CLAUDE.md` | This file — the curriculum's constitution |
