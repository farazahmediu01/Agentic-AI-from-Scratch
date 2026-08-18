# The Chapter Playbook

> **Read this before building any chapter.** It is the blueprint a fresh session picks up so the work continues in the same direction, at the same bar, without rediscovering what already cost us time.
>
> `CLAUDE.md` holds the **rules** (why the curriculum is shaped this way).
> `INSTRUCTOR.md` holds the **teaching practice** (how to deliver it).
> This holds the **build process** (how to author the next chapter).

---

## 0. Start here — the five-minute orientation

A fresh session, in this order:

1. **`CLAUDE.md`** — loaded automatically. The roadmap table tells you which chapter is next and its status. The Chapter Completion State section tells you what every built chapter contains and what defects it deliberately carries.
2. **This file** — the process below.
3. **The most recent built chapter's `README.md`** — for voice, structure and pacing. Copy its shape, not its content.
4. **`git log --oneline -10`** — the commit messages in this repo are deliberately long and carry the reasoning behind decisions.

Then confirm the environment before writing anything:

```powershell
uv run python -m shared.models    # which provider/model, costs nothing
uv run pytest -q                  # should be green
```

---

## 1. The three things that must never drift

If a decision conflicts with one of these, the decision is wrong.

**① The destination is SDK fluency.** A graduate opens a blank file and writes a working, tool-using, evaluated SDK agent unaided. Hand-rolling exists to make the SDK legible and for no other reason. When you catch yourself building something interesting that is not agent-building — a schema generator, a parser, a tracer — **stop.** That failure has a name here: *the means ate the goal*, and it is why the curriculum was rewritten.

**② Practice follows every concept.** No section explains something without asking the student to do something. If a section is pure prose, it is unfinished.

**③ Honest numbers.** Every chapter header carries Core and Full, every section is `[core]` or `[depth]`, and the header equals the sum of its own task estimates. If you add 20 minutes of content, update the header in the same edit. This is not bookkeeping — the old "~4 hrs" claim was the single most damaging line in the repo.

---

## 2. The build sequence

Follow the order. It was arrived at by doing it wrong first.

### Phase A — Specify (no code)

1. Read the previous chapter's *"What this chapter cannot do"* section. **That is your opening hook**, already written for you.
2. Assign each concept a depth using the table in `CLAUDE.md`. If a concept is not in that table, add it there with a one-line justification.
3. Decide what is `[core]` and what is `[depth]`, with minute estimates.
4. **Write the spec into `CLAUDE.md`** — sections, budgets, the tracks, and any decisions taken with their rationale. Do this *before* building, so a session that dies mid-build loses nothing.
5. Surface genuine forks to the user. Do not guess on anything that changes the shape of the work.

### Phase B — Code first, prose second

> **The rule that matters most in this file.** Write and *run* the code before writing the README. Chapter 3's §1 originally had invented tool outputs; the real captured run was better, and it exposed a defect the invented version had papered over. Chapter 0's async timings had to be measured — "about 3× faster" would have been a guess; `1.51s vs 0.62s` is a lesson.

Build in this order, running each piece as you finish it:

| # | Build | Then |
|---|---|---|
| 1 | The spike, if the depth policy calls for one (≤60 lines) | **Run it. Paste real output into the README later** |
| 2 | The `with_sdk/` demo | Run it. Verify against the real provider |
| 3 | The spine increment | Run it once end to end |
| 4 | The offline `test_*.py` | `uv run pytest` |
| 5 | Wire `pyproject.toml` — see §4 | `uv run pyright` |
| 6 | The full gate | All four clean |

### Phase C — Write the chapter

7. `README.md`, using the **real outputs** you captured.
8. `EXERCISES.md` — Track 1 drills in a rotating throwaway domain. **Never expenses.** At least half SDK-native.
9. `PROJECT.md` — Track 2 spine increment + the verbatim Track 3 block + Spendly Transfer.
10. `SDK_BRIDGE.md` — the chapter's rows, plus a "what does NOT transfer" note.
11. Update the roadmap in **`CLAUDE.md` and root `README.md` together.** They must never disagree; three contradictory roadmaps shipped once.

### Phase D — Verify

12. Run the golden dataset. **See §5 — this is where chapters actually fail.**
13. Fix real defects. Document each one in place.
14. Write `solutions/RUNS.md` with the model name, the date, and the actual output.
15. Commit with a message that explains the *reasoning*, not the file list.

---

## 3. Definition of done

A chapter is not finished until every box is true.

**Structure**
- [ ] Concept → practice → (challenge) throughout; no prose-only section
- [ ] Every section marked `[core]` or `[depth]` with a minute estimate
- [ ] Header budget equals the sum of those estimates
- [ ] At least one **blank-file, unaided** task, marked mandatory
- [ ] Opens by re-reading the previous chapter's code as a new kind of question
- [ ] Closes by naming what this chapter *cannot* do

**Content**
- [ ] Any spike is ≤60 lines and marked disposable in its docstring
- [ ] `with_sdk/` hand-rolls nothing the SDK provides
- [ ] Track 1 drills use a rotating non-expense domain
- [ ] Track 3 block is copy-pasted verbatim
- [ ] An honest-limitation section in the §7b/§8 tradition

**Proof**
- [ ] Gate clean: `ruff format`, `ruff check`, `pyright` 0/0, `pytest`
- [ ] Golden dataset passes **in one run, on one model**
- [ ] **Every prior chapter's cases still pass** (the regression rule)
- [ ] `RUNS.md` records model, date and real output
- [ ] `CLAUDE.md` completion state updated, including any defects left in deliberately

---

## 4. Wiring a new chapter into the gate

Three files, and forgetting any one produces a confusing failure.

**`pyproject.toml`** — three separate places:

```toml
[tool.ruff]
src = [..., "0N_chapter/examples", "0N_chapter/solutions", "0N_chapter/exercises"]

[tool.pyright]
include = [..., "0N_chapter"]

[[tool.pyright.executionEnvironments]]     # one block PER script-style folder
root = "0N_chapter/solutions"
extraPaths = ["0N_chapter/solutions"]      # + any earlier chapter it imports

[tool.pytest.ini_options]
testpaths = [..., "0N_chapter"]
```

**Why one `executionEnvironments` block per folder:** every chapter has its own `tools.py` imported by bare name. A flat `extraPaths` resolves them all to whichever came first.

**Runtime is separate from pyright.** `extraPaths` is a *type-checking* setting; it does not put anything on `sys.path`. A chapter importing an earlier chapter's modules needs a `_bootstrap.py` — see `03_structured_outputs/solutions/_bootstrap.py` and its docstring.

---

## 5. Verification protocol

Golden-dataset runs are where time disappears. Budget them.

### Quota

The binding free-tier limit is the **per-day** one — quotaId `GenerateRequestsPerDayPerProjectPerModel-FreeTier`. Not the famous ~15/minute one.

- One full dataset run is **60–90 requests**.
- ⚠️ **The daily cap is per model AND differs wildly between models.** Read `quotaValue` in the 429 body — it is printed every time. Measured Aug 2026: `gemini-3.5-flash-lite` **500/day**, `gemini-3.5-flash` **20/day**. A 20/day model cannot finish one dataset run, so *"switch to any other model"* is bad advice on its own — switch to one you have checked.
- Exhausted? **Switch `MODEL_NAME` to a different, verified Gemini model.** A second key in the same project shares the exhausted bucket.
- You do **not** need to edit `.env` — `load_dotenv()` never overrides an existing environment variable, so a shell prefix wins for one command: `MODEL_NAME=gemini-3.6-flash uv run python .../check_multiturn.py`. Prefer this; `.env` holds the user's key.
- ⚠️ **Not every model can run the spine.** From Ch3 on it needs `output_type=` **and** tools *together*, and some models refuse the combination with a `400 INVALID_ARGUMENT`: *"Function calling with a response mime type: 'application/json' is unsupported"*. `gemini-2.5-flash` fails this way. Verified working Aug 2026: `gemini-3.5-flash`, `gemini-3.5-flash-lite`, `gemini-3.6-flash`.
- **Probe a new model with one request before betting a 15-minute run on it** — one tool, one `output_type`, one prompt. A whole multi-turn run was lost to skipping this.
- **Read the `quotaId` in a 429 before tuning a retry.** Two full runs were lost to backoff tuned against the wrong limit. Both limits are real and need different fixes:

| quotaId | Limit | Fix |
|---|---|---|
| `GenerateRequestsPerMinutePerProjectPerModel-FreeTier` | 15/min | pacing — `await asyncio.sleep(8)` between runs |
| `GenerateRequestsPerDayPerProjectPerModel-FreeTier` | **model-specific** — 500/day on flash-lite, 20/day on flash | a different model, from the verified list |

Demos that fire runs back to back hit the per-minute one; dataset harnesses that pause between cases hit the per-day one.

### Reading a failure

Always diagnose the *shape* before touching the agent:

| Shape | Cause | Do |
|---|---|---|
| `branch=none  turns=0`, `waiting…` lines above | Quota. The SDK burns `max_turns` under sustained 429s and raises `MaxTurnsExceeded` | Switch model or wait. Re-run with `--only` |
| A real branch, some checks FAIL | **Genuine defect** | Read the check label — it names the field and the value |
| Passes on re-run | Non-determinism | Run 3× before changing anything |

**If a dataset is flaky, fix the harness before the agent.** An eval that fails for infrastructure reasons teaches nothing and costs you trust in the suite.

### When a case genuinely fails

1. **Check the assertion first.** Is the expected behaviour actually right? Do not weaken a check to make a run pass.
2. Ask which layer should own the fix: **a type** makes the failure impossible to express, **a schema** makes it impossible to hide, **a cross-check** makes it impossible to ship, **a prompt** does none of the three and only lowers the rate.
3. After narrowing any rule, **re-run the case that depended on the old behaviour.** Narrowing the refusal rule for case 6 could easily have broken case 7; checking was the point.
4. Document the defect in place. A found bug beats an invented example, and this repo's best pages are all real failures.

---

## 6. Gotchas that have already cost time

- **Non-ASCII in `print()` mangles on the Windows console.** Em-dashes, arrows and smart quotes render as `?`. Use plain ASCII inside `print()` and in file docstrings that get printed. Markdown prose is fine — it is never written to a terminal.
- **`sys.stdout.reconfigure` needs an `isinstance(sys.stdout, io.TextIOWrapper)` narrow**, because `sys.stdout` is typed as the `TextIO` protocol.
- **Long harnesses must line-buffer.** Python block-buffers stdout when redirected, so a 15-minute run shows nothing until the end and looks exactly like a hang.
- **`RUF100` flags `noqa` for rules you have not enabled.** Do not copy `noqa` comments from other repos.
- **`asyncio.run` requires a `Coroutine`, not an `Awaitable`.** Type aliases for async callables need `Callable[[X], Coroutine[Any, Any, Y]]`.
- **A keyword call cannot be checked against a positional `Callable`.** A registry dispatched with `**kwargs` needs `Callable[..., X]`.
- **Pydantic lax mode coerces `True` to `1`.** Fine for a model's sloppy JSON, catastrophic for a money field.
- **Never assert on turn count in an eval.** The SDK batches parallel tool calls differently from a hand-rolled loop.

---

## 7. Anti-patterns — the specific ways this repo has gone wrong

Each of these actually happened.

| Anti-pattern | What it looked like | The rule now |
|---|---|---|
| **The means ate the goal** | 60–90 min rebuilding a Pydantic-model-generating decorator | Hand-roll only what a student must picture while debugging |
| **Dishonest budgets** | Header said ~4 hrs; the file's own tasks summed to 9–11 | Header equals the sum, always |
| **Contradictory roadmaps** | Three shipped at once, disagreeing about Chapter 3 | One roadmap. Change it everywhere in one edit |
| **A lying front door** | "Basic Python" for a chapter needing decorators and `async` | Never describe the prerequisite as "basic Python" |
| **Recognition mistaken for fluency** | Every SDK task was read/predict/modify | Every chapter has a mandatory blank-file task |
| **One domain for everything** | ~40 tasks across arithmetic and expenses | Drills rotate. Never expenses |
| **Blaming the agent for the harness** | 25/58 from rate limiting, nearly "fixed" as an agent bug | Diagnose the failure shape first |
| **Prose before code** | Invented tool outputs in a README draft | Run it, then write what happened |

---

## 8. Where things get written down

| Discovery | Goes in |
|---|---|
| A rule about how the curriculum works | `CLAUDE.md` |
| A defect found while building | In the code, **and** the chapter README, **and** `CLAUDE.md`'s completion state |
| Something that will bite the next author | §6 of this file |
| Something an instructor needs in a room | `INSTRUCTOR.md` |
| What a run actually produced | `solutions/RUNS.md` |
| Why a decision was made | The commit message |

> **The test for whether a session is safe to compact:** could a fresh session build the next chapter correctly using only the repo? If something lives only in the conversation, write it down first.
