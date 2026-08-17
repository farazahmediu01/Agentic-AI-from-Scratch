# Teaching this curriculum

> The front door for instructors. `CLAUDE.md` is the constitution — the rules and why they exist. This is the operating manual: what to do, in what order, and what will go wrong.

---

## 1. What you actually have

**Four chapters, ≈34 hours of core path.** That is a real 10–12 week module, not a workshop.

| Ch | Title | Core | Full |
|---|---|---|---|
| 0 | Python for Agents | 6 hrs | 7.5 |
| 1 | The Agent Loop | 8 hrs | 11.5 |
| 2 | Typed Tools | 11 hrs | 18–20 |
| 3 | Structured Outputs | 9 hrs | 14.5 |

Chapters 4+ are a published hypothesis, not a promise. Each is specified only after the previous one is built and validated — see the roadmap in `CLAUDE.md`. **Do not schedule a cohort past Chapter 3.**

### Read the budget table correctly

Every chapter header carries **two** numbers, and every section is marked `[core]` or `[depth]`:

- **Core** — the critical path. A student who finishes core is ready for the next chapter with nothing missing.
- **Full** — core plus every depth block, challenge and optional drill.

**Teach core. Skip `[depth]` in class.** Those blocks exist for the student who wants them and for you when a question goes deep. Putting them in a session plan is how you fall three weeks behind by week four.

If a header's number ever disagrees with the sum of its own task estimates, that is a bug in the repo. Report it.

---

## 2. Step 0 — work the whole thing as a student first

**Non-negotiable, and the step people skip.** Budget the full 34 hours before your first session.

Do the practices. Do the blank-file drills. Build Spendly Lite. **Pick your own Track 3 agent and actually build it** — you cannot grade a track you have never done.

The reason is not diligence. This curriculum's best moments are surprises, and you cannot stage a surprise you have not had:

| Moment | You need to have |
|---|---|
| Ch2 `break_it.py` | been genuinely startled that `add(a="5", b="3")` returns `"53"` |
| Ch3 spike | watched 3 of 8 responses survive `json.loads` after a prompt that begged for clean JSON |
| Ch3 §1 | seen a perfect tool chain produce a confidently wrong sentence |
| Ch0 experiment 4 | felt `asyncio.sleep` and `time.sleep` produce a 3× difference in identical code |

Finish by getting the gate green yourself:

```powershell
uv run ruff format . ; uv run ruff check . ; uv run pyright ; uv run pytest
```

---

## 3. The per-chapter prep loop

Do this in the week before each chapter. **Every time**, including chapters you have taught before.

| # | Do | Why |
|---|---|---|
| 1 | Read the chapter README end to end | You are teaching from it |
| 2 | Re-read the Depth Policy in `CLAUDE.md` | It tells you what is droppable, and why |
| 3 | Decide **your** core/depth line for this cohort | The marks are a default, not a ruling |
| 4 | **Re-run the chapter's golden dataset** | Models drift. What the model did last term is not what it does today |
| 5 | Re-run `uv run pytest` | Your fast smoke test |

**Step 4 is the one that matters.** It takes ~15 minutes and it tells you what today's model actually does before twenty students find out simultaneously.

```powershell
uv run python 02_typed_tools/solutions/check_expenses.py
uv run python 03_structured_outputs/solutions/check_expenses.py
```

---

## 4. The session shape

**A chapter is 2–3 sessions of 90–120 minutes.** Not one.

| Phase | Time | What |
|---|---|---|
| Concept + inline practice | 40–50 min | One concept, then they type. **Never more than ~8 minutes of talking before hands move** |
| Drills (Track 1) | 30–40 min | Rotating domain. You circulate |
| Debrief | 10–15 min | What broke. Then name what this chapter *cannot* do — that is next session's hook |
| Project | Lab / homework | Tracks 2 and 3, both with `RUNS.md` |

### Four teaching moves that carry the design

**Don't show the code first.** Mental model, then ask them to predict, then reveal. The `<details>` spoilers exist for this — make students commit to an answer out loud before you open one. A prediction they got wrong is worth ten explanations.

**Run before reading.** Output first, trace backward.

**Let exercises fail.** The guided builds are engineered so students hit real bugs. Preempting the failure destroys the lesson. `break_it.py` before the fix, always.

**Connect forward, every time.** End each session by naming the limitation the current chapter cannot solve. Ch1 ends at "the model can call your function wrongly." Ch2 ends at "nothing checks the output." Ch3 ends at "it has no memory." That chain is the spine of the course.

---

## 5. The three tracks, in a room

Three things run in parallel. This is where instructors get confused, so be explicit with students on day one.

| Track | Where | Domain | Who grades | How |
|---|---|---|---|---|
| 1️⃣ **Drills** | In class | Rotating throwaway — dice, weather, recipes, library | You, informally | Does it run |
| 2️⃣ **Spine** | Homework | Expenses, always | The golden dataset | Objective, automated |
| 3️⃣ **Own agent** | Homework | **Student's choice** | The 4-line rubric | **Evidence, not features** |

### Protect Track 3

Students pick their domain in the **Chapter 1 session** — make it a live 10-minute activity, not a homework line. A student who never picks never starts, and by Chapter 3 they have no portfolio piece.

Enforce one rule without exception: **it must not be an expense tracker.** The whole point of a second domain is that they cannot pattern-match their way through it.

And grade it the way the rubric says:

```
[ ] The chapter's capability is present and working in YOUR agent
[ ] RUNS.md has 3 new runs, dated, with actual output pasted in
[ ] One paragraph: what broke, and what you changed
[ ] It is not an expense tracker
```

**A rough agent that broke, with the breakage documented, passes. A polished agent with no `RUNS.md` fails.** Students will fight you on this exactly once. Holding the line is what teaches them that evidence is the deliverable — which is the actual job.

### The regression rule

From Chapter 2 on, every prior chapter's dataset cases must still pass. A chapter that breaks Chapter 1's cases is not finished, however good its new feature is.

Say this out loud when you introduce it. It is most students' first encounter with the idea that *not breaking things* is part of the work.

---

## 6. Grading

| Instrument | Covers | Objectivity |
|---|---|---|
| The gate (`ruff`/`pyright`/`pytest`) | Every submission | Binary |
| Golden dataset | Track 2 | Objective, automated |
| Track 3 rubric | Track 3 | Evidence-based, identical every chapter |
| Blank-file drills | Ch2 Practice 12, Ch3 §10 | Did they produce, unaided |

**The blank-file drills are the real assessment.** Everything else tests recognition or modification. Recognition, recall and generation are three different competencies, and only generation is fluency. If a student passes every dataset case but cannot open an empty file and write a working SDK agent, they have not learned this.

---

## 7. Classroom gotchas

**Rate limits will bite you.** Free Gemini is ~15 requests/minute *per key*. Every student needs their own. One agent run is 4–10 requests. Tell them 429s are normal and not their bug.

**Never put a golden dataset in class time.** Ch3's is ~15 minutes of mostly waiting. It is homework, or you run it during prep.

**Rate limiting wears a costume.** This is the single most confusing failure your students will hit, so teach it before it happens:

> Under sustained rate limiting, the SDK absorbs the 429 internally, hands the run loop an unusable response, and burns through `max_turns` in seconds. What escapes is **`MaxTurnsExceeded`**, not `RateLimitError`. A quota problem arrives looking exactly like an agent that would not stop talking.
>
> **The tell is the clock.** Real max-turns exhaustion takes a while. Quota exhaustion is instant, and the case output shows `branch=none turns=0`.
>
> The general lesson is worth more than the workaround: *an exception type tells you where a failure surfaced, not what caused it.*

**Model drift will break a demo eventually.** When it does, that **is** the lesson — it is the reason the eval suite exists. Do not hide it or pre-record around it.

**Ch3's spike is deliberately offline.** It replays 8 captured responses so the whole room sees the same failures at the same moment. Use the offline run for teaching; run `--live` once, in front of them, to make the point that you cannot enumerate a sampler's failure modes.

**The gate is a hard gate.** "It works on my machine" is not a completion criterion. Students copy what they see, and a teaching repo has no excuse for a lower bar than a production one.

---

## 8. A realistic calendar

Assuming one 2-hour session per week plus homework:

| Weeks | Chapter | In class | Homework |
|---|---|---|---|
| 1–3 | 0 — Python for Agents | 4 hrs | 2 hrs |
| 4–7 | 1 — The Agent Loop | 5 hrs | 3 hrs |
| 8–12 | 2 — Typed Tools | 6 hrs | 5 hrs |
| 13–16 | 3 — Structured Outputs | 5 hrs | 4 hrs |

**Do not compress Chapter 0.** It is the chapter that decides whether Chapter 2 is possible, and it has a diagnostic at the top precisely so you can compress it *per student* instead of for everyone.

Run the Chapter 0 diagnostic as a live 15-minute activity in session one. Students who score 6/6 skip to Chapter 1 and start their Track 3 agent early. Students who score 0–2 now know exactly which sections they need, instead of concluding they are bad at Python.

---

## 9. Troubleshooting

| Symptom | Almost always |
|---|---|
| `MaxTurnsExceeded`, `turns=0` | Rate limit. Wait, re-run with `--only` |
| Dataset case fails once, passes next time | Model non-determinism. Run 3× before changing anything |
| Every case fails at once | Environment — key, quota or `.env`. Run `uv run python -m shared.models` |
| `ModuleNotFoundError: expense_store` in Ch3 | Missing `import _bootstrap`. Read that file's docstring |
| pyright errors only in one chapter folder | Missing `executionEnvironments` block in `pyproject.toml` |
| Student's agent invents data | Design problem, not a bug. Ch3 §6 — a required field is an instruction to always have an answer |

**If a dataset is flaky, fix the harness before you touch the agent.** An eval that fails for infrastructure reasons teaches nothing and costs you trust in the suite — and trust in the suite is the thing the whole back half of this curriculum runs on.

---

## 10. What to say on day one

Students arriving from web development expect to `pip install` a framework and be productive. Set the frame before they open a file:

> *"You will spend the first four chapters learning what a framework does, so that when it breaks — and it breaks constantly — you are debugging a system you understand instead of a black box. Then you will use the framework for everything, forever, because that is what professionals do. The hand-rolling is a teaching device, not the job."*

Then tell them the honest bit:

> *"Roughly a third of what you build here will fail in ways nobody planned. That is not the course going wrong. Agents are non-deterministic, and learning to prove one works is the actual skill."*

That second sentence prevents more dropouts than any amount of encouragement, because it reframes the failures they are about to hit as the curriculum working rather than as evidence they cannot do this.
