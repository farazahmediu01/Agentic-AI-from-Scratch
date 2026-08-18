"""
Spendly Lite v4 — the agent that remembers, and the agent that knows who it is
talking to.

    uv run python 04_sessions_state/solutions/expense_agent_v4.py

WHAT CHANGED FROM v3
--------------------
Three things, and it is worth reading the list before the code because the list
is shorter than anybody expects for a chapter titled "Sessions & State":

    1.  run_expense_agent(..., session=...)     one keyword argument
    2.  get_budget(ctx, category)               one extra parameter on one tool
    3.  Agent[User](...)                        one type parameter

That is the whole chapter at the code level. Chapter 3's output contract is
imported unchanged. Chapter 2's tools and storage are imported unchanged. If
adding memory to an agent had required rewriting its tools, the memory would
have been in the wrong place.

WHAT DID *NOT* CHANGE, AND WHY IT IS THE POINT
-----------------------------------------------
`SYSTEM_PROMPT` gains no instruction to "remember the conversation". There is
nowhere to put one that would help: the model does not choose to remember. The
session puts the previous turns back into the request, and a model that can read
its own transcript needs no encouragement to use it.

> **Compare that with Chapter 3.** There, `output_type=` handled the SHAPE and
> four paragraphs of prompt handled the JUDGEMENT, because branch selection is a
> judgement. Here there is no judgement to make, so the prompt is silent. Ask of
> every new primitive: does this replace a rule I was writing in English? If it
> does, delete the English. If it does not, the prompt still owns that job.

THE ONE PROMPT LINE THAT DID CHANGE
------------------------------------
See `PERSONAL BUDGETS` below. It exists because per-user budgets create a new
way for the model to be confidently wrong -- reciting a figure it saw in a
previous conversation, or worse, one it half-remembers from its training data
about "typical" budgets. This is the Chapter 1 rule ("use tools for every fact")
arriving in a world where there is finally a plausible-looking memory to recall
from instead. Chapter 4 section 8 is about exactly this.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from agents import Agent, Runner, SQLiteSession, function_tool
from agents.exceptions import ModelBehaviorError
from agents.items import ToolCallItem, ToolCallOutputItem
from agents.memory.session import Session
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
from spendly_context import User, default_user

MODEL = make_model()

REJECTED_PREFIX = "INVALID ARGUMENTS"

# Where multi-turn conversations are persisted. Gitignored via `**/data/`, the
# same rule that covers the ledger, and for the same reason: it is run state,
# not source.
SESSION_DB = Path(__file__).parent / "data" / "sessions.db"


# -----------------------------------------------------------------------------
# THE PROMPT RULE THAT BECAME A FABRICATION INSTRUCTION.
#
# `USING WHAT YOU WERE ALREADY TOLD` was added for one reason: case M1 needs the
# agent to treat a one-word "Groceries." as the answer to a question it asked a
# turn ago. The rule did that, and it also broke the control.
#
# Case M2 runs those same two turns with NO session. Given "Groceries." and an
# empty transcript, the agent read the rule, concluded it must have asked, and
# called log_expense with a vendor and an amount nobody had ever given it.
#
# > **A rule written to exploit memory becomes an instruction to invent when the
# > memory is absent.** The rule never said "check that you can see it" -- it did
# > not need to while a session was always attached, and every test that had one
# > passed.
#
# This is the fourth member of the family the curriculum has been narrowing:
# Ch2 7b the model FABRICATED a value from nothing, Ch3 1 it MISCOMPUTED one from
# real tool output, Ch3 case 8 it INFERRED a plausible one from context, and here
# it BACKFILLED one from a conversation that never happened.
#
# The fix is a prompt fix, correctly: nothing about the shape was wrong. The reply
# was a flawless `Logged`. Only the world it described was imaginary.
#
# It was caught by M2, which exists only as a control. **An eval with no control
# cannot tell "the session works" from "the model guessed well" -- and it also
# cannot tell you when the thing you added to make the session work has quietly
# taught the agent to lie without one.**
# -----------------------------------------------------------------------------

SYSTEM_PROMPT = """You are Spendly, a careful personal expense assistant. All amounts are in PKR.

How to work:
- Use tools for every fact. Never recall a total or a budget from memory.
- Log an expense only when you know the vendor, the amount and the category.
- If something is missing, ask the user. Do not guess and do not use a placeholder.
- Read the tool's own reply before answering. Never claim you logged something
  unless the tool told you it was logged.

PERSONAL BUDGETS. Budgets belong to the person you are talking to, not to Spendly.
- get_budget returns THIS user's budget. There is no standard budget, no typical
  budget, and no budget you can reason your way to. Call the tool.
- A figure from earlier in this conversation is not a fact, it is a quote. If the
  ledger has changed since -- or if you are not certain it has not -- call the
  tool again. Re-reading a number is cheap; reporting a stale one is not.

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
  REFORMATTING IS NOT CORRECTING. If the date is unambiguous but written in
  another format -- "05/08/2026 (the 5th of August)" -- convert it to
  YYYY-MM-DD and carry on. That is reading what they said, not inventing it.
  Refuse a date only when it is impossible, in the future, or genuinely
  ambiguous with no clarification given.
- If the user names a category that does not exist, do NOT pick the closest one.
  Call list_categories and let them choose.
- If the user does not name a category AT ALL, do not infer one. A vendor's name
  is not a category: "Metro" does not tell you the money went on groceries, and
  guessing correctly most of the time is still guessing. Ask which category.
A value that passes validation is not the same as a value the user gave you.

USING WHAT YOU WERE ALREADY TOLD. If an earlier turn in this conversation supplied
a value, it is supplied. Do not ask for it twice. If you asked which category an
expense belongs to and the user answers with a category name, that answer completes
the expense you were asking about.
  BUT "earlier in this conversation" means a message you can actually SEE above
  this one. If the vendor and the amount are not in front of you, you do not have
  them -- no matter how strongly a one-word reply implies that somebody asked a
  question. A short message with nothing above it is the START of a conversation,
  not the end of one. Ask. Never fill a gap with a value you cannot point at.

CHOOSING YOUR REPLY SHAPE. Set exactly ONE of the four fields, never zero, never two:
- `logged`         : you called log_expense and the tool confirmed it was written.
- `reported`       : you answered a question about existing spending. Nothing was written.
- `need_more_info` : a required value was missing, so you did nothing and are asking.
                     List what is missing in `missing`.
- `refused`        : the user gave a value you must not act on -- a negative or zero
                     amount, an impossible or future date, a category that does not
                     exist. Echo their value verbatim in `offending_value`. Do not
                     fix it.
                     `refused` is the LAST resort, not the safe default. A value you
                     can read but must reformat is not a refusal. A tool rejecting
                     your arguments once is not a refusal either -- read the error,
                     fix the format, and call it again.

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
# The tools. Six are Chapter 2's, wrapped and unchanged. ONE has a new first
# parameter, and that one parameter is the entire dependency-injection lesson.
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
def get_budget(ctx: RunContextWrapper[User], category: Category) -> float:
    """Get the monthly budget in PKR for one category."""
    # THE ONE CHANGED TOOL.
    #
    # `ctx` is first, and it is not in the schema the model reads -- the SDK
    # strips a leading RunContextWrapper parameter before generating the tool
    # definition. Print `get_budget.params_json_schema` and check: the model is
    # told about `category` and nothing else.
    #
    # That asymmetry is the whole primitive. The model decides WHICH category to
    # ask about; your application decides WHOSE budget answers. Neither can do
    # the other's job, and neither can see the other's input.
    #
    # Contrast the alternative you have probably written before: putting the
    # user's budgets into the system prompt. It works, and it costs you three
    # things -- the numbers are now tokens you pay for on every turn, they are
    # visible to anyone who can make the model repeat its instructions, and the
    # model can round them.
    return ctx.context.budget_for(category)


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


# `Agent[User]` rather than `Agent`. At runtime this changes nothing whatsoever.
# At edit time it is the difference between pyright checking `ctx.context.name`
# and pyright shrugging at it, because an unparameterised Agent's context is
# `Any` and `Any` accepts every typo you will ever write. Chapter 0's point about
# type hints doing real work, arriving on an agent.
agent = Agent[User](
    name="Spendly Lite v4",
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


def make_session(session_id: str, *, persistent: bool = True) -> SQLiteSession:
    """
    One conversation's memory.

    `session_id` is the only thing separating one user's conversation from
    another's, and it is a plain string with no validation behind it. Chapter 4
    section 4 is about the consequences of that sentence.
    """
    if not persistent:
        # ':memory:' -- dies with the process. Right for tests, wrong for a
        # product, and the default in the SDK's own constructor.
        return SQLiteSession(session_id)
    SESSION_DB.parent.mkdir(parents=True, exist_ok=True)
    return SQLiteSession(session_id, SESSION_DB)


@dataclass
class SdkRun:
    """
    Chapter 3's adapter with TWO new fields, both about growth.

    `input_tokens` is the one to watch. It is the number of tokens the provider
    charged you for reading, this turn -- which under a session means "the whole
    conversation so far, again". Section 9 plots it and the shape of that plot is
    Chapter 5's entire justification.
    """

    reply: SpendlyReply | None
    final_answer: str
    iterations: int = 0
    tool_names: list[str] = field(default_factory=list)
    executed_names: list[str] = field(default_factory=list)
    hit_max_iterations: bool = False
    tool_arguments: list[tuple[str, str]] = field(default_factory=list)
    output_error: str = ""
    input_tokens: int = 0
    session_items: int = 0
    # The transcript as JSON, after this turn. Empty when no session is attached.
    #
    # It exists because of a check that was WRONG on its first outing. Case M3
    # asserts that one conversation cannot hear another, and it originally proved
    # that by asserting `session_items <= 2` -- a proxy, and a bad one, because a
    # run adds its OWN items to the session it is running in. It failed at 6.
    #
    # The temptation is to raise the number until it passes. That is how a suite
    # stops meaning anything. The claim being made is "Metro is not in this
    # conversation", so the assertion should be exactly that -- which needs the
    # transcript, not a count of it.
    session_text: str = ""

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


async def _run_with_backoff(
    prompt: str,
    max_turns: int,
    user: User,
    session: Session | None,
    attempts: int = 4,
) -> Any:
    """
    Carried forward from Chapter 3. Read its docstring for why the transient set
    contains MaxTurnsExceeded -- a quota failure arrives dressed as a runaway
    agent, and diagnosing from the exception type alone cost a whole run.

    ONE THING IS DIFFERENT NOW, and it is a genuine hazard rather than a detail.

    A retry inside a session is not a clean retry. `Runner.run` writes the user's
    message to the session as it starts, so an attempt that dies mid-run can
    leave the message behind. Retrying then appends it a second time, and the
    model sees the user saying the same thing twice.

    We accept that here, for one reason worth stating out loud: the alternative
    is for the harness to reach into the session and pop items after a failure,
    and a test harness that repairs the thing it is testing is not a test
    harness. The cases below are two turns long and the duplicate is harmless.
    In a product it is not harmless, and `pop_item()` is the tool for it --
    section 2b of the README.
    """
    delay = 20.0
    for attempt in range(1, attempts + 1):
        try:
            return await Runner.run(
                agent, prompt, max_turns=max_turns, context=user, session=session
            )
        except Exception as exc:
            name = type(exc).__name__
            transient = {
                "RateLimitError",
                "MaxTurnsExceeded",
                "APITimeoutError",
                "APIConnectionError",
                "InternalServerError",
            }
            retryable = name in transient or "429" in str(exc)
            if not retryable or attempt == attempts:
                raise
            why = {
                "MaxTurnsExceeded": "turns burnt (probably quota)",
                "APITimeoutError": "request timed out",
                "APIConnectionError": "connection dropped",
                "InternalServerError": "provider 5xx",
            }.get(name, "429 quota")
            print(f"  [{why} - waiting {delay:.0f}s, attempt {attempt}]")
            await asyncio.sleep(delay)
            delay *= 1.8
    raise RuntimeError("unreachable")


async def run_expense_agent(
    prompt: str,
    *,
    user: User | None = None,
    session: Session | None = None,
    max_turns: int = 15,
) -> SdkRun:
    """
    One turn.

    Both new arguments default to the Chapter 1-3 behaviour -- `session=None` is
    a stateless run, and `user=None` is the single hard-coded user those chapters
    assumed. That is not politeness towards old code; it is what lets
    `check_regression.py` push Chapter 3's nine cases through this function
    unmodified and get Chapter 3's answers.
    """
    who = user or default_user()
    try:
        result = await _run_with_backoff(prompt, max_turns, who, session)
    except Exception as exc:
        name = type(exc).__name__
        if name == "MaxTurnsExceeded":
            return SdkRun(
                reply=None,
                final_answer=f"[max turns exceeded: {exc}]",
                hit_max_iterations=True,
            )
        if name in {"ModelBehaviorError", "UserError"}:
            return SdkRun(reply=None, final_answer="", output_error=f"{name}: {exc}")
        raise

    calls = [item for item in result.new_items if isinstance(item, ToolCallItem)]
    outputs = [item for item in result.new_items if isinstance(item, ToolCallOutputItem)]

    names = [str(getattr(c.raw_item, "name", "?")) for c in calls]
    rejected = [str(o.output).startswith(REJECTED_PREFIX) for o in outputs]
    reply = result.final_output
    stored = await session.get_items() if session is not None else []

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
        input_tokens=result.context_wrapper.usage.input_tokens,
        session_items=len(stored),
        session_text=json.dumps(stored),
    )


async def main() -> None:
    """
    The demo Chapter 3 could not run: an expense logged across two turns.

    Chapter 3's case 8 ended with the agent asking a perfectly typed question --
    `missing == ["category"]` -- that nothing in the system could hear the answer
    to. Watch the second turn. The user says one word.
    """
    expense_store.reset(seeded=True)
    session = make_session("demo_chapter4", persistent=False)
    user = default_user()

    turns = ["Log 500 at Metro.", "Groceries."]

    for number, prompt in enumerate(turns, start=1):
        print(f"\nTURN {number}  USER: {prompt}")
        print("-" * 72)
        run = await run_expense_agent(prompt, user=user, session=session)
        for name, args in run.tool_arguments:
            print(f"  -> {name}({args})")
        print(f"  branch        : {run.branch}")
        print(f"  session items : {run.session_items}")
        print(f"  input tokens  : {run.input_tokens}")
        print(f"  reply         : {run.reply!r}")

    print("\n" + "=" * 72)
    rows = [r for r in expense_store.all_expenses() if r["notes"] != "seed"]
    print(f"ledger now holds {len(rows)} new row(s): {rows}")
    print(
        "\nThe second turn was one word. It became a complete expense because the\n"
        "vendor and the amount were still in the transcript. That is the chapter."
    )


if __name__ == "__main__":
    asyncio.run(main())
