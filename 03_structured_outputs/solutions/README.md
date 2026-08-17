# Chapter 3 — reference solutions

**Open these after you attempt, not before.** Reading the answer first feels efficient and teaches nothing.

| File | What it is |
|---|---|
| `replies.py` | **The chapter.** The four-branch output contract, and `exactly_one_branch` — the curriculum's first guardrail |
| `expense_agent_v3.py` | Spendly Lite v3. Chapter 2's tools unchanged, plus `output_type=` and one prompt section |
| `check_expenses.py` | The 9-case golden dataset. **Zero substring assertions** |
| `test_replies.py` | 11 offline tests, no API key, ~0.1s — including one that passes on fabricated data on purpose |
| `_bootstrap.py` | The `sys.path` shim that "one continuous spine" costs. Read its docstring; the lesson is real |

## Run them

```powershell
uv run python 03_structured_outputs/solutions/expense_agent_v3.py    # one run, ~30s
uv run pytest 03_structured_outputs/                                 # free, offline, instant
uv run python 03_structured_outputs/solutions/check_expenses.py      # 9 cases, ~6 minutes
```

## What is different about this chapter's solutions

**There is no second build.** Chapters 1 and 2 had `expense_agent.py` *and* `expense_agent_sdk.py`. From here the spine is SDK-only — see `PROJECT.md` for why, and `CLAUDE.md` for the rule.

**The storage and tools are imported, not copied.** `expense_store.py` and `expense_tools.py` live in `02_typed_tools/solutions/` and are used from there unchanged. That they needed no changes to gain an output contract is the strongest evidence Chapter 2 drew its boundary in the right place.

**The dataset asserts on fields.** Every check reads a value off a typed object. If you find yourself unable to express an assertion without `in answer`, that is a signal the output model is missing a field — not a reason to reach for a substring.
