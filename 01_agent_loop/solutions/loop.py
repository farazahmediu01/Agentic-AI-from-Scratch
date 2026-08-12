"""
Reference agent loop — the same five steps as `agent.py`, with two upgrades
the exercises ask for:

  1. It returns a structured `AgentRun` instead of a bare string (Exercise 5).
  2. The tool registry and schemas are *parameters*, not imports, so one loop
     can drive many different agents (used by unit_agent.py and invoice_agent.py).

Notice what #2 means: the moment you parameterise the loop over its tools,
you have written `Agent(tools=[...])`. That is genuinely most of what a
framework's Agent class is. Everything else it sells you is convenience on
top of this file.
"""

from __future__ import annotations

import json
import os
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam, ChatCompletionToolParam

# Higher than agent.py's 10: the invoice project legitimately needs ~7 iterations
# (rate -> line totals -> subtotal -> discount -> tax -> save -> answer), and a
# chattier model can take a couple more. Set the ceiling above the *expected*
# worst case, not at it — otherwise the circuit breaker fires on correct runs
# and students debug a bug that doesn't exist.
MAX_ITERATIONS = 15
MAX_SECONDS = 180.0

# The Gemini free tier allows ~15 requests/minute. One agent run is 6-8 requests,
# so two runs back to back will trip a 429. Retrying with backoff is not optional
# polish — without it, every multi-case check run dies halfway through.
MAX_RETRIES = 5


@dataclass
class ToolCallRecord:
    """One executed tool call — what was asked, what came back, did it blow up."""

    name: str
    arguments: dict
    result: str
    errored: bool


@dataclass
class AgentRun:
    """
    Everything that happened during one run.

    Returning this instead of a string is what makes an agent *testable*:
    you can assert on which tools ran, not just on the final prose.
    """

    final_answer: str
    iterations: int = 0
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    hit_max_iterations: bool = False
    stopped_on_timeout: bool = False

    @property
    def tool_names(self) -> list[str]:
        return [tc.name for tc in self.tool_calls]

    @property
    def error_count(self) -> int:
        return sum(1 for tc in self.tool_calls if tc.errored)

    def summary(self) -> str:
        counts: dict[str, int] = {}
        for name in self.tool_names:
            counts[name] = counts.get(name, 0) + 1
        used = ", ".join(f"{n}({c})" for n, c in counts.items()) or "none"
        return (
            "\n=== RUN SUMMARY ===\n"
            f"Iterations used     : {self.iterations} / {MAX_ITERATIONS}\n"
            f"Tool calls executed : {len(self.tool_calls)}\n"
            f"Tool errors         : {self.error_count}\n"
            f"Tools used          : {used}\n"
            f"Final message length: {len(self.final_answer)} chars"
        )


def _create_with_retry(
    client: OpenAI,
    model: str,
    messages: list[ChatCompletionMessageParam],
    tool_schemas: list[ChatCompletionToolParam],
    verbose: bool,
) -> ChatCompletion:
    """
    Call the model, backing off on 429s instead of crashing the run.

    A rate limit is a *transient* failure — the correct response is to wait and
    retry, not to lose the whole conversation. Note the asymmetry with tool
    errors: those get handed to the model to reason about, because the model can
    do something about them. A 429 is ours to handle; the model cannot help.
    """
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
                print(
                    f"  ! rate limited — retrying in {delay:.0f}s (attempt {attempt}/{MAX_RETRIES})"
                )
            time.sleep(delay)
            delay *= 2  # exponential backoff
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
    tool_registry: dict[str, Callable],
    tool_schemas: list[ChatCompletionToolParam],
    system_prompt: str | None = None,
    verbose: bool = True,
) -> AgentRun:
    """Run the loop until the model stops calling tools, or a budget trips."""
    client, model = _make_client()
    started = time.monotonic()

    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    run = AgentRun(final_answer="")

    for iteration in range(1, MAX_ITERATIONS + 1):
        run.iterations = iteration
        if verbose:
            print(f"\n--- Iteration {iteration} ---")

        # Second circuit breaker: wall-clock. Iterations are a proxy for cost,
        # seconds are a proxy for the user's patience. Both deserve a ceiling.
        if time.monotonic() - started > MAX_SECONDS:
            run.stopped_on_timeout = True
            run.final_answer = f"[Agent stopped after {MAX_SECONDS:.0f}s time budget.]"
            return run

        # STEP 1 — send the whole conversation.
        response = _create_with_retry(client, model, messages, tool_schemas, verbose)

        # STEP 2 — parse. Preserve the assistant turn verbatim; the API needs it
        # so the tool results below can link back by tool_call_id.
        assistant_message = response.choices[0].message
        messages.append(
            cast(ChatCompletionMessageParam, assistant_message.model_dump(exclude_none=True))
        )

        if not assistant_message.tool_calls:
            run.final_answer = assistant_message.content or ""
            if verbose:
                print("Model returned a final answer — exiting loop.")
            return run

        if verbose:
            print(f"Model requested {len(assistant_message.tool_calls)} tool call(s):")

        # STEP 3 + 4 — execute each call, append each result.
        for tool_call in assistant_message.tool_calls:
            if tool_call.type != "function":
                continue

            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments
            errored = False

            try:
                tool_args = json.loads(raw_args) if raw_args else {}
            except json.JSONDecodeError as exc:
                tool_args = {}
                errored = True
                print(f"  ! Failed to parse arguments for {tool_name}: {exc}")

            if verbose:
                print(f"  -> {tool_name}({tool_args})")

            try:
                tool_fn = tool_registry[tool_name]
                tool_result = tool_fn(**tool_args)
                result_str = (
                    tool_result if isinstance(tool_result, str) else json.dumps(tool_result)
                )
            except KeyError:
                errored = True
                result_str = (
                    f"ERROR: unknown tool '{tool_name}'. "
                    f"Available tools: {', '.join(sorted(tool_registry))}"
                )
            except Exception as exc:
                errored = True
                result_str = f"ERROR: {type(exc).__name__}: {exc}"

            if verbose:
                print(f"     <- {result_str}")

            run.tool_calls.append(
                ToolCallRecord(
                    name=tool_name,
                    arguments=tool_args,
                    result=result_str,
                    errored=errored,
                )
            )

            # STEP 5 (prep) — the result goes back into the conversation.
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result_str})

    run.hit_max_iterations = True
    run.final_answer = (
        f"[Agent reached max iterations ({MAX_ITERATIONS}) without completing the task.]"
    )
    return run
