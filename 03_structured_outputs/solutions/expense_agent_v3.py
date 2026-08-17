"""
Spendly Lite v3 — SDK build, with a contract on the output.

    uv run python 03_structured_outputs/solutions/expense_agent_v3.py

WHY THERE IS NO SECOND BUILD IN THIS CHAPTER
--------------------------------------------
Chapters 1 and 2 built the spine twice, by hand and on the SDK, and graded both
with one dataset. That was worth doing: a second implementation of a
non-deterministic system is a second behavioural sample, for free.

Chapter 3 is where it stops, and the reason is specific rather than fatigue.
The hand-rolled version of this mechanism is `from_scratch/prompt_and_parse.py`,
and section 3 of the README spends twenty-five minutes proving it cannot be made
correct. Shipping the spine on top of it to preserve a symmetry would be
teaching a practice we had just finished disproving.

So: the spike demonstrates the mechanism and is deleted. The spine is SDK-only
from here. That rule is written down in `CLAUDE.md` under "The Taper Rule".

WHAT CHANGED FROM v2
--------------------
Two things, and only two:

    +  output_type=SpendlyReply
    +  four paragraphs in the prompt telling the model which branch means what

The seven tools are imported from Chapter 2 unchanged. The storage layer is
imported from Chapter 2 unchanged. If adding an output contract had forced a
rewrite of either, the boundary between them was in the wrong place.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from typing import Any

from agents import Agent, Runner, function_tool
from agents.exceptions import ModelBehaviorError
from agents.items import ToolCallItem, ToolCallOutputItem
from agents.run_context import RunContextWrapper
from agents.tool_context import ToolContext
from pydantic import ValidationError

import _bootstrap  # noqa: F401  -- must precede every spine import; see _bootstrap.py
import expense_store
import expense_tools as t
from expense_store import Category
from expense_tools import Amount, IsoDate, Limit, Month, Vendor
from replies import SpendlyReply
from shared.models import make_model

MODEL = make_model()

REJECTED_PREFIX = "INVALID ARGUMENTS"

TASK = "I spent 1500 at KFC on lunch today. Log it, then tell me what's left of my food budget."


# -----------------------------------------------------------------------------
# The prompt. Chapter 2's, plus one new section.
#
# Note what the new section does NOT do: it does not describe the JSON format,
# list the keys, or beg for valid syntax. The schema handles all of that. What
# the prompt still owns is WHICH BRANCH MEANS WHAT -- a judgement, not a shape.
#
# That division is the chapter in one paragraph. Shape moved into the type.
# Judgement stayed in the prompt, because it was always judgement.
# -----------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Spendly, a careful personal expense assistant. All amounts are in PKR.

How to work:
- Use tools for every fact. Never recall a total or a budget from memory.
- Log an expense only when you know the vendor, the amount and the category.
- If something is missing, ask the user. Do not guess and do not use a placeholder.
- Read the tool's own reply before answering. Never claim you logged something
  unless the tool told you it was logged.

REPORTING NUMBERS. Every figure you report must be a value a tool returned, copied
exactly. Never adjust one, and never do arithmetic yourself:
- To get budget remaining: call log_expense FIRST, then month_total (so the total
  includes what you just logged), then subtract(budget, month_total). Report the
  number subtract gave you, unchanged.
- month_total already includes the expense you just logged. Do NOT subtract that
  expense a second time.
- If a number you want to report is not a value some tool handed you, you are
  about to invent it. Call a tool instead.

NEVER SILENTLY CORRECT THE USER'S DATA. This is the rule that types cannot enforce:
- If the user gives a negative or zero amount, do NOT make it positive. Refuse,
  say why, and ask them to confirm what they actually spent.
- If the user gives a date that cannot be used, do NOT substitute today's date.
  Tell them what is wrong with the date they gave and ask for the real one.
- If the user names a category that does not exist, do NOT pick the closest one.
  Call list_categories and let them choose.
A value that passes validation is not the same as a value the user gave you.

CHOOSING YOUR REPLY SHAPE. Set exactly ONE of the four fields, never zero, never two:
- `logged`         : you called log_expense and the tool confirmed it was written.
- `reported`       : you answered a question about existing spending. Nothing was written.
- `need_more_info` : a required value was missing, so you did nothing and are asking.
                     List what is missing in `missing`.
- `refused`        : the user gave a value you must not act on -- a negative or zero
                     amount, an unusable date, a category that does not exist. Echo
                     their value verbatim in `offending_value`. Do not fix it.

If you both logged something and reported a budget figure, that is ONE `logged`
reply with `remaining` filled in -- not two branches."""


def explain_to_model(ctx: RunContextWrapper[Any], error: Exception) -> str:
    """Carried forward from Chapter 2 unchanged."""
    tool_name = ctx.tool_name if isinstance(ctx, ToolContext) else "the tool"
    cause = error.__cause__

    if isinstance(error, ModelBehaviorError) and isinstance(cause, ValidationError):
        lines = [
            f"  - {'.'.join(str(p) for p in e['loc']) or '(whole object)'}: "
            f"{e['msg']} (you sent: {e.get('input')!r})"
            for e in cause.errors()
        ]
        return (
            f"{REJECTED_PREFIX} for tool '{tool_name}'. Nothing was executed.\n"
            + "\n".join(lines)
            + f"\nFix the arguments and call '{tool_name}' again. If the correct value "
            f"is something the user never told you, ask them for it. Do not invent it."
        )

    return f"{REJECTED_PREFIX} for tool '{tool_name}'. Nothing was executed.\n  - {error}"


# -----------------------------------------------------------------------------
# The same seven tools, imported from Chapter 2 and wrapped. Unchanged.
# -----------------------------------------------------------------------------


@function_tool(failure_error_function=explain_to_model)
def get_today() -> str:
    """Return today's date as YYYY-MM-DD."""
    return t.get_today.fn()


@function_tool(failure_error_function=explain_to_model)
def log_expense(
    vendor: Vendor,
    amount: Amount,
    category: Category,
    expense_date: IsoDate = "",
) -> str:
    """
    Record one expense in the user's ledger.

    This is the only tool here that changes anything. Call it only when the
    vendor, the amount and the category are all known.
    """
    return t.log_expense.fn(vendor, amount, category, expense_date)


@function_tool(failure_error_function=explain_to_model)
def month_total(category: Category, month: Month = "") -> float:
    """Total amount already spent in one category during one month."""
    return t.month_total.fn(category, month)


@function_tool(failure_error_function=explain_to_model)
def get_budget(category: Category) -> float:
    """Get the monthly budget in PKR for one category."""
    return t.get_budget.fn(category)


@function_tool(failure_error_function=explain_to_model)
def subtract(a: float, b: float) -> float:
    """Subtract b from a. Use it to compute budget remaining: subtract(budget, spent)."""
    return t.subtract.fn(a, b)


@function_tool(failure_error_function=explain_to_model)
def list_recent(limit: Limit = 5) -> str:
    """List the most recently recorded expenses, newest last."""
    return t.list_recent.fn(limit)


@function_tool(failure_error_function=explain_to_model)
def list_categories() -> str:
    """List every valid expense category."""
    return t.list_categories.fn()


agent = Agent(
    name="Spendly Lite v3",
    instructions=SYSTEM_PROMPT,
    model=MODEL,
    output_type=SpendlyReply,
    tools=[
        get_today,
        log_expense,
        month_total,
        get_budget,
        subtract,
        list_recent,
        list_categories,
    ],
)


@dataclass
class SdkRun:
    """
    The adapter, carried forward from Chapter 2 with ONE new field.

    `reply` is the typed object. `final_answer` survives only so the Chapter 1
    and Chapter 2 dataset cases still run against this build -- the regression
    rule. Note how thin it has become: a string squeezed out of a typed object
    purely for backwards compatibility.
    """

    reply: SpendlyReply | None
    final_answer: str
    iterations: int = 0
    tool_names: list[str] = field(default_factory=list)
    executed_names: list[str] = field(default_factory=list)
    hit_max_iterations: bool = False
    tool_arguments: list[tuple[str, str]] = field(default_factory=list)
    output_error: str = ""

    @property
    def rejected_count(self) -> int:
        return len(self.tool_names) - len(self.executed_names)

    @property
    def branch(self) -> str:
        return self.reply.branch if self.reply is not None else "none"


def _flatten(reply: SpendlyReply) -> str:
    """Squash a typed reply back into one sentence, for the older cases only."""
    for name in ("logged", "reported", "need_more_info", "refused"):
        branch = getattr(reply, name)
        if branch is None:
            continue
        return str(getattr(branch, "reply", None) or getattr(branch, "question", ""))
    return ""


async def _run_with_backoff(prompt: str, max_turns: int, attempts: int = 4) -> Any:
    """
    Retry on free-tier exhaustion. Read the second condition carefully -- it took
    a wrong diagnosis to find, and it is the more interesting of the two.

    Chapter 1's hand-rolled `loop.py` retried 429s. Moving to `Runner.run` lost
    that silently: the SDK retries some transport failures but not a provider
    quota error, and nothing warned us. **When you adopt a framework, the things
    you built that it does not provide do not announce themselves on the way
    out.** They are simply gone, and you find out in the first noisy demo.

    So the obvious fix is to catch `RateLimitError` here. That is not enough, and
    the first version of this harness scored 25/58 because of it.

    Under sustained rate limiting the SDK's own retry layer absorbs the 429 and
    hands the run loop a response it cannot use. The loop tries again, absorbs
    another 429, tries again -- and burns through `max_turns` in a couple of
    seconds. What finally escapes is **MaxTurnsExceeded**, not RateLimitError. A
    quota problem arrives wearing the costume of an agent that would not stop
    talking, and every check in that case fails for a reason that has nothing to
    do with the agent.

    Hence the second condition. A genuine runaway agent will exhaust its turns
    again on the retry and fail honestly; a rate-limited one will pass. The tell
    is the clock: real max-turns exhaustion takes a while, quota exhaustion is
    instant.

    > Generalise it: **an exception type tells you where a failure surfaced, not
    > what caused it.** Diagnosing from the type alone is how you end up
    > "fixing" an agent that was never broken.
    """
    delay = 20.0
    for attempt in range(1, attempts + 1):
        try:
            return await Runner.run(agent, prompt, max_turns=max_turns)
        except Exception as exc:
            name = type(exc).__name__
            retryable = name == "RateLimitError" or "429" in str(exc) or name == "MaxTurnsExceeded"
            if not retryable or attempt == attempts:
                raise
            why = "turns burnt (probably quota)" if name == "MaxTurnsExceeded" else "429 quota"
            print(f"  [{why} - waiting {delay:.0f}s, attempt {attempt}]")
            await asyncio.sleep(delay)
            delay *= 1.8
    raise RuntimeError("unreachable")


async def run_expense_agent(prompt: str, max_turns: int = 15) -> SdkRun:
    try:
        result = await _run_with_backoff(prompt, max_turns)
    except Exception as exc:
        name = type(exc).__name__
        if name == "MaxTurnsExceeded":
            return SdkRun(
                reply=None,
                final_answer=f"[max turns exceeded: {exc}]",
                hit_max_iterations=True,
            )
        # A model that produces a shape the schema rejects lands here. In v2 this
        # was impossible, because any string at all was an acceptable answer.
        if name in {"ModelBehaviorError", "UserError"}:
            return SdkRun(reply=None, final_answer="", output_error=f"{name}: {exc}")
        raise

    calls = [item for item in result.new_items if isinstance(item, ToolCallItem)]
    outputs = [item for item in result.new_items if isinstance(item, ToolCallOutputItem)]

    names = [str(getattr(c.raw_item, "name", "?")) for c in calls]
    rejected = [str(o.output).startswith(REJECTED_PREFIX) for o in outputs]
    reply = result.final_output

    return SdkRun(
        reply=reply,
        final_answer=_flatten(reply),
        iterations=len(result.raw_responses),
        tool_names=names,
        executed_names=[
            name
            for index, name in enumerate(names)
            if not (index < len(rejected) and rejected[index])
        ],
        tool_arguments=[
            (str(getattr(c.raw_item, "name", "?")), str(getattr(c.raw_item, "arguments", "")))
            for c in calls
        ],
    )


async def main() -> None:
    expense_store.reset(seeded=True)

    print(f"USER: {TASK}")
    print("=" * 72)

    run = await run_expense_agent(TASK)

    print(f"Tool calls attempted ({len(run.tool_names)}):")
    for name, args in run.tool_arguments:
        print(f"  -> {name}({args})")

    print("=" * 72)
    print(f"\nbranch  : {run.branch}")
    print(f"turns   : {run.iterations}")
    if run.output_error:
        print(f"OUTPUT ERROR: {run.output_error}")
    print(f"\nreply object:\n{run.reply!r}\n")


if __name__ == "__main__":
    asyncio.run(main())
