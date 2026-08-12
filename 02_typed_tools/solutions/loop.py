"""
The reusable loop for Chapter 2 — Chapter 1's `loop.py` with a boundary.

Diff it against `../../01_agent_loop/solutions/loop.py`. Four changes, all of
them on the Trust axis:

  1. `tools: list[Tool]` replaces `tool_registry` + `tool_schemas`. Two
     parameters that had to agree with each other became one that cannot
     disagree with itself.
  2. Dispatch is `tool.call(raw)` — parse and validate before the body runs.
  3. `ToolCallRecord` gains `rejected`, so a run can be asked "how many calls
     never reached a function body?" That number is the chapter's proof.
  4. `MAX_INVALID_CALLS` — a second circuit breaker, on the model's accuracy
     rather than on its verbosity.

Everything else — the 429 backoff, the wall-clock budget, the AgentRun shape —
is Chapter 1's, unchanged. New capability should cost new code, not a rewrite.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from openai.types.chat import (
    ChatCompletion,
    ChatCompletionMessageParam,
    ChatCompletionToolParam,
)

from chapter import Tool, ToolError, registry, schemas

MAX_ITERATIONS = 15
MAX_SECONDS = 180.0
MAX_RETRIES = 5

# How many rejected tool calls before we stop the run.
#
# Set it above the number of retries a CORRECT recovery needs, not at it. One
# rejection followed by a fixed call is healthy behaviour and must not trip the
# breaker; three rejections in a run means the model cannot read the contract,
# and further turns are just money.
MAX_INVALID_CALLS = 4


@dataclass
class ToolCallRecord:
    """One tool call the model attempted."""

    name: str
    raw_arguments: str
    result: str
    rejected: bool = False  # failed validation — the function body never ran
    failed: bool = False  # the body ran and raised


@dataclass
class AgentRun:
    """Everything that happened during one run."""

    final_answer: str
    iterations: int = 0
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    hit_max_iterations: bool = False
    stopped_on_timeout: bool = False
    stopped_on_invalid_calls: bool = False

    @property
    def tool_names(self) -> list[str]:
        return [tc.name for tc in self.tool_calls]

    @property
    def executed_names(self) -> list[str]:
        """
        Tools that actually RAN.

        Chapter 1 could not draw this distinction: every call reached a function
        body, so "called" and "ran" were the same word. Now they are not, and
        the difference is what an eval should assert on. `log_expense` appearing
        in `tool_names` no longer means anything was written.
        """
        return [tc.name for tc in self.tool_calls if not tc.rejected]

    @property
    def rejected_count(self) -> int:
        return sum(1 for tc in self.tool_calls if tc.rejected)

    def summary(self) -> str:
        counts: dict[str, int] = {}
        for name in self.tool_names:
            counts[name] = counts.get(name, 0) + 1
        used = ", ".join(f"{n}({c})" for n, c in counts.items()) or "none"
        return (
            "\n=== RUN SUMMARY ===\n"
            f"Iterations used     : {self.iterations} / {MAX_ITERATIONS}\n"
            f"Tool calls attempted: {len(self.tool_calls)}\n"
            f"Rejected at boundary: {self.rejected_count}\n"
            f"Failed inside body  : {sum(1 for tc in self.tool_calls if tc.failed)}\n"
            f"Tools attempted     : {used}\n"
            f"Final message length: {len(self.final_answer)} chars"
        )


def _create_with_retry(
    client: OpenAI,
    model: str,
    messages: list[ChatCompletionMessageParam],
    tool_schemas: list[ChatCompletionToolParam],
    verbose: bool,
) -> ChatCompletion:
    """Call the model, backing off on 429s instead of crashing the run."""
    delay = 5.0
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return client.chat.completions.create(
                model=model, messages=messages, tools=tool_schemas
            )
        except RateLimitError:
            if attempt == MAX_RETRIES:
                raise
            if verbose:
                print(f"  ! rate limited - retrying in {delay:.0f}s (attempt {attempt})")
            time.sleep(delay)
            delay *= 2
    raise RuntimeError("unreachable")


def _make_client() -> tuple[OpenAI, str]:
    load_dotenv()
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )
    return client, os.environ.get("MODEL_NAME", "gemini-2.5-flash")


def run_agent(
    user_message: str,
    tools: list[Tool],
    system_prompt: str | None = None,
    verbose: bool = True,
) -> AgentRun:
    """Run the loop until the model stops calling tools, or a budget trips."""
    client, model = _make_client()
    started = time.monotonic()

    tools_by_name = registry(tools)
    tool_schemas = schemas(tools)

    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    run = AgentRun(final_answer="")

    for iteration in range(1, MAX_ITERATIONS + 1):
        run.iterations = iteration
        if verbose:
            print(f"\n--- Iteration {iteration} ---")

        if time.monotonic() - started > MAX_SECONDS:
            run.stopped_on_timeout = True
            run.final_answer = f"[Agent stopped after {MAX_SECONDS:.0f}s time budget.]"
            return run

        response = _create_with_retry(client, model, messages, tool_schemas, verbose)

        assistant_message = response.choices[0].message
        messages.append(
            cast(ChatCompletionMessageParam, assistant_message.model_dump(exclude_none=True))
        )

        if not assistant_message.tool_calls:
            run.final_answer = assistant_message.content or ""
            if verbose:
                print("Model returned a final answer - exiting loop.")
            return run

        if verbose:
            print(f"Model requested {len(assistant_message.tool_calls)} tool call(s):")

        for tool_call in assistant_message.tool_calls:
            if tool_call.type != "function":
                continue

            name = tool_call.function.name
            raw = tool_call.function.arguments
            rejected = False
            failed = False

            if verbose:
                print(f"  -> {name}({raw})")

            tool = tools_by_name.get(name)
            if tool is None:
                rejected = True
                result = (
                    f"ERROR: there is no tool called '{name}'. "
                    f"Available tools: {', '.join(sorted(tools_by_name))}."
                )
            else:
                try:
                    result = tool.call(raw)
                except ToolError as exc:
                    # The contract was violated, or a business rule inside the
                    # body raised deliberately. Either way the model can act on
                    # it, so it goes back into the conversation.
                    rejected = True
                    result = str(exc)
                except Exception as exc:
                    # Our bug, not the model's. Say so and do not invite a retry.
                    failed = True
                    if verbose:
                        print(f"     !! internal failure: {type(exc).__name__}: {exc}")
                    result = (
                        f"ERROR: the tool '{name}' failed internally. You cannot fix "
                        f"this by changing the arguments. Tell the user the tool is "
                        f"unavailable and stop retrying it."
                    )

            if verbose:
                print(f"     <- {result}")

            run.tool_calls.append(
                ToolCallRecord(
                    name=name,
                    raw_arguments=raw,
                    result=result,
                    rejected=rejected,
                    failed=failed,
                )
            )
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

        # Checked after the results are appended, so the model's last rejection
        # is on record in the transcript we return.
        if run.rejected_count >= MAX_INVALID_CALLS:
            run.stopped_on_invalid_calls = True
            run.final_answer = (
                f"[Agent stopped: {run.rejected_count} tool calls were rejected at the "
                f"boundary. The model could not produce arguments matching the contracts.]"
            )
            return run

    run.hit_max_iterations = True
    run.final_answer = f"[Agent reached max iterations ({MAX_ITERATIONS}).]"
    return run
