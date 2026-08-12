"""
Step 1 — The Agent Loop, from scratch.

The five-step loop the entire agentic-AI field is built on:

    1. Send the conversation so far to the LLM.
    2. Parse what the model returned.
    3. If it asked to call a tool, execute the tool.
    4. Append the tool's result back into the conversation.
    5. Go to step 1.

The loop ENDS when the model returns a normal text reply with no tool calls.
That's the model's way of saying "I'm done — here's the final answer."

Read this file top to bottom. Every line earns its place.
"""

from __future__ import annotations

import json
import os
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from tools import TOOL_REGISTRY, TOOL_SCHEMAS

# Production discipline rule #1: never let an agent loop run forever.
# A misbehaving model + a buggy tool can burn $100 in an hour. The ceiling
# is your circuit breaker. We'll formalize this idea in later steps.
MAX_ITERATIONS = 10


def run_agent(user_message: str, system_prompt: str | None = None) -> str:
    """
    Run the agentic loop until the model returns a final answer or we hit
    MAX_ITERATIONS. Returns the final assistant message text.

    `messages` is the running conversation. Each turn we:
      - append the user message (first iteration only)
      - send the whole history to the model
      - append the model's response to history
      - if the model wants tools, run them and append their results
      - loop
    """
    load_dotenv()
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )
    model = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

    # The conversation is just a list of dicts. That's it. No magic state.
    # The model sees exactly what's in this list, every turn.
    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- Iteration {iteration} ---")

        # ------------------------------------------------------------------
        # STEP 1: Send the conversation to the LLM.
        # ------------------------------------------------------------------
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=TOOL_SCHEMAS,
        )

        # ------------------------------------------------------------------
        # STEP 2: Parse the model's response.
        # The response always has exactly one of these shapes:
        #   (a) plain text content  -> final answer, we're done.
        #   (b) one or more tool_calls -> we need to execute them and keep looping.
        # ------------------------------------------------------------------
        assistant_message = response.choices[0].message

        # Preserve the assistant message in history *exactly as the model emitted it*.
        # The API requires this on the next turn so tool results can link back
        # to the original tool_call_id.
        messages.append(
            cast(ChatCompletionMessageParam, assistant_message.model_dump(exclude_none=True))
        )

        # No tool calls means the model is finished. This is the loop exit.
        if not assistant_message.tool_calls:
            print("Model returned a final answer — exiting loop.")
            return assistant_message.content or ""

        # ------------------------------------------------------------------
        # STEP 3 + 4: Execute each tool call, append each result.
        # The model can request multiple tools in one turn (parallel calls).
        # We run them sequentially here for simplicity.
        # ------------------------------------------------------------------
        print(f"Model requested {len(assistant_message.tool_calls)} tool call(s):")
        for tool_call in assistant_message.tool_calls:
            if tool_call.type != "function":
                continue
            tool_name = tool_call.function.name
            raw_args = tool_call.function.arguments

            # Tool arguments arrive as a JSON *string*. Parse them.
            try:
                tool_args = json.loads(raw_args) if raw_args else {}
            except json.JSONDecodeError as exc:
                tool_args = {}
                print(f"  ! Failed to parse arguments for {tool_name}: {exc}")

            print(f"  -> {tool_name}({tool_args})")

            # Dispatch through the registry. Wrap in try/except so a buggy
            # tool can't crash the entire agent — instead we feed the error
            # back to the model and let it decide what to do.
            try:
                tool_fn = TOOL_REGISTRY[tool_name]
                tool_result = tool_fn(**tool_args)
                result_str = (
                    tool_result if isinstance(tool_result, str) else json.dumps(tool_result)
                )
            except KeyError:
                result_str = f"ERROR: unknown tool '{tool_name}'"
            except Exception as exc:
                result_str = f"ERROR: {type(exc).__name__}: {exc}"

            print(f"     <- {result_str}")

            # ------------------------------------------------------------------
            # STEP 5 (prep): append the tool's result so the model sees it next turn.
            # role="tool" is special — it tells the API "this is the output of
            # the tool with id=tool_call_id from the previous assistant turn."
            # ------------------------------------------------------------------
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result_str,
                }
            )

        # The for-loop falls through to the next iteration -> back to STEP 1.

    # Production discipline rule #1 in action: we ran out of budget.
    return f"[Agent reached max iterations ({MAX_ITERATIONS}) without completing the task.]"


if __name__ == "__main__":
    task = (
        "What's the current time? Also, calculate 15 multiplied by 7, "
        "then add 23 to that result. Give me a single clean summary at the end."
    )

    print(f"USER TASK:\n  {task}")
    print("=" * 72)

    final_answer = run_agent(
        user_message=task,
        system_prompt=(
            "You are a careful assistant. Use the available tools to answer "
            "the user's question step by step. Chain tool calls when one "
            "result feeds the next. When you have everything you need, stop "
            "calling tools and write a clean final summary."
        ),
    )

    print("=" * 72)
    print(f"\nFINAL ANSWER:\n{final_answer}\n")
