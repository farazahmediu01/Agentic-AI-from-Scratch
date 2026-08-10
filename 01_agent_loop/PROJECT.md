# Chapter 1 Project — The Freelance Invoice Agent

> **Every chapter ends with a project.** Practice tasks teach one concept each. Exercises stretch them. The project makes you assemble all of them into one thing that works.

**Time: 90–120 minutes. Build it in `project/` inside this folder.**

---

## The Brief

A freelancer describes their month in plain English. The agent turns that into a correct, itemised invoice saved to disk.

```
You: I did 12 hours of backend work and 6.5 hours of UI design for Acme Corp this month.
     Apply the 10% loyalty discount and 5% tax. Save the invoice.

Agent: [calls lookup_rate, multiply, add, apply_discount, apply_tax, save_invoice ...]

        Invoice INV-20260810-1432 saved to invoices/INV-20260810-1432.txt
        Subtotal PKR 113,750 | Discount -PKR 11,375 | Tax PKR 5,118.75 | Total PKR 107,493.75
```

Nothing here is beyond Chapter 1. No memory, no context management, no framework — a loop, tools, schemas, a registry, and a system prompt.

**Why this project:** it needs *genuine* multi-step chaining (you cannot compute the total without three earlier tool results), it has a real side effect (a file gets written), and it has failure paths (unknown role, negative hours) that force the error-handling concept to earn its keep.

---

## Required Tools

Implement in `project/invoice_tools.py`. All pure Python — no network calls.

| Tool | Signature | Behaviour |
|------|-----------|-----------|
| `get_current_time` | `() -> str` | ISO timestamp — used for the invoice date and ID |
| `lookup_rate` | `(role: str) -> float` | Hourly rate from a dict. **Raise a helpful error for unknown roles, listing the valid ones.** |
| `line_total` | `(hours: float, rate: float) -> float` | Hours × rate. **Reject negative hours with a clear error.** |
| `add` | `(a: float, b: float) -> float` | Sum two line totals into a subtotal |
| `apply_discount` | `(amount: float, percent: float) -> float` | Amount after discount |
| `apply_tax` | `(amount: float, percent: float) -> float` | Amount after tax |
| `save_invoice` | `(client: str, lines: str, subtotal: float, discount: float, tax: float, total: float) -> str` | Writes `invoices/INV-<timestamp>.txt`, returns the path |

Rate card (use exactly this so results are checkable):

```python
RATE_CARD: dict[str, float] = {
    "backend":   6500.0,
    "frontend":  6000.0,
    "ui design": 5500.0,
    "devops":    7000.0,
    "consulting": 9000.0,
}
```

---

## Required Behaviour

1. **Multi-step chaining.** `line_total` results feed `add`; the subtotal feeds `apply_discount`; that feeds `apply_tax`; all of it feeds `save_invoice`. The agent must discover this order itself — do not hardcode a pipeline.
2. **A real artifact.** A readable `.txt` invoice file exists on disk after a successful run.
3. **Graceful failure.** `"I did 5 hours of underwater welding"` must produce a helpful reply listing valid roles — not a crash, not an invented rate.
4. **Refusal to guess.** If hours or the client name are missing, the agent asks for them instead of inventing values. (System-prompt work — Exercise 2's skill.)
5. **Safety limits.** `MAX_ITERATIONS` is enforced and the exhaustion path returns an honest message.
6. **Observability.** Every run prints the summary from Exercise 3: iterations used, tool calls, tool errors, tools used.

---

## Required Files

```
01_agent_loop/project/
  invoice_agent.py     # the loop (start from agent.py, then make it yours)
  invoice_tools.py     # 7 tools + schemas + registry
  check_invoice.py     # assertion-based checks (from Exercise 5)
  RUNS.md              # evidence — 5 recorded runs
  invoices/            # generated output (gitignored is fine)
```

### `RUNS.md` is not optional

Five runs, recorded in this table. **Fill in `Expected` before you run.**

| # | Input | Expected | Actual | Tools called | Iterations | Pass? |
|---|-------|----------|--------|--------------|------------|-------|
| 1 | 12h backend, 6.5h ui design, Acme, 10% disc, 5% tax | Total 107,493.75 | | | | |
| 2 | 8h devops only, no discount, 5% tax | Total 58,800 | | | | |
| 3 | 5h underwater welding | Helpful refusal, no file written | | | | |
| 4 | "make me an invoice" (nothing else) | Asks for client, role, hours | | | | |
| 5 | -3h backend | Rejects negative hours | | | | |

For any failing row, add a sentence on **why** it failed and what you changed.

> This is your first golden dataset. Five hand-written cases with expected outputs is exactly what Step 5 automates — building it by hand now means the eval harness will feel obvious later, instead of feeling like framework magic.

---

## Acceptance Checklist

You are done when **every box** is checked:

**Functionality**
- [ ] `uv run python 01_agent_loop/project/invoice_agent.py` runs end to end
- [ ] Run 1 produces subtotal 113,750 / discount 11,375 / tax 5,118.75 / **total 107,493.75**
      (12 × 6500 = 78,000 · 6.5 × 5500 = 35,750 · −10% · +5%)
- [ ] An invoice file exists in `invoices/` and is human-readable
- [ ] All five `RUNS.md` rows are filled in with real observed output

**Correctness of the loop**
- [ ] The trace shows ≥ 5 tool calls across ≥ 3 iterations for run 1
- [ ] At least one tool call demonstrably consumes another tool's output
- [ ] No arithmetic is done by the model in its head — every number in the final answer traces to a tool result

**Robustness**
- [ ] Unknown role → helpful message listing valid roles, and **no file written**
- [ ] Negative hours → rejected with a clear error
- [ ] Missing information → the agent asks instead of inventing

**Engineering**
- [ ] `uv run pyright 01_agent_loop/project/` → **0 errors, 0 warnings**
- [ ] `check_invoice.py` passes with ≥ 5 assertions covering tools used, iteration count, and the final total
- [ ] No API key in source — `.env` only
- [ ] No agent framework imported

---

## Grading Rubric (for instructors)

| Band | Score | What it looks like |
|------|-------|--------------------|
| **Excellent** | 90–100 | All boxes checked. Tool descriptions are precise and the model never mis-selects. Errors are written *for the model to act on*. `RUNS.md` includes a failure the student diagnosed and fixed. |
| **Good** | 75–89 | Runs correctly on the happy path; one robustness case is weak. Checks exist but are shallow (only asserts the final string). |
| **Needs work** | 60–74 | Works only on the exact demo input. Model does some arithmetic itself. `RUNS.md` filled in after the fact with no real expectations. |
| **Incomplete** | < 60 | Hardcoded pipeline instead of model-driven tool selection, or no artifact produced. |

**The single most common failure:** the student hardcodes the call order in Python because "the model kept getting it wrong." That is a pipeline, not an agent. The fix is always better tool descriptions and a sharper system prompt — never an `if` statement in the loop.

### The trap in Run 5 (worth the whole project)

Almost every first attempt fails Run 5, and it fails in a way that looks like a pass.

`line_total` raises on negative hours, so the tool is "guarded". But the model reads `-3 hours`, decides it's obviously a typo, helpfully passes `3` to the tool, and the guard never fires. A confident, wrong invoice gets saved.

**A validation check only protects you if the bad value actually reaches it.** The model sits upstream of every guard you write, and it is trained to be helpful — which includes silently cleaning up input. The fix is defence in depth: a rule in the system prompt where the *decision* is made, plus the `raise` where the *work* is done. Neither layer alone is enough.

If a student's Run 5 passes on the first try, ask to see the arguments `line_total` actually received. Often the tool was never called at all — and that's the right answer for the wrong reason unless they can explain why.

---

## Stretch Goals (optional)

1. **Multi-client batch** — one request producing three separate invoices.
2. **Approval gate** — reuse Exercise 7 so `save_invoice` requires human `y/N` confirmation.
3. **Markdown output** — a `save_invoice_md` tool, letting the model choose the format based on what the user asked for.
4. **Currency conversion** — a `convert_currency(amount, to_currency)` tool with a static rate table, so a client can be billed in USD.

---

## Ship It

- [ ] Commit with a message describing what the agent does, not what files changed
- [ ] Write a short LinkedIn post: *the one thing that surprised you about making the model chain tool calls correctly*. Include your `RUNS.md` table as the proof.

Then, and only then, move to **Step 2 — Manual Tool Use**, where we throw away the `tools=` shortcut and hand-roll the schema generation and parsing underneath it.
