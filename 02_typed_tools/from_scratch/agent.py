"""
Chapter 2 — the loop, with a boundary.

    uv run python 02_typed_tools/from_scratch/agent.py

Diff this against `../../01_agent_loop/from_scratch/agent.py`. The five steps
are untouched. Three things changed, and all three are on the Trust axis:

  1. `tools=` is a list of `Tool` objects. The schemas are generated, not typed
     out by hand, so the contract and the code cannot drift apart.
  2. Dispatch goes through `tool.call(raw_arguments)`, which parses and
     validates before your function body is reached.
  3. A ToolError does not end the run. It goes back into the conversation and
     the model gets another attempt -- but only a bounded number of them.

Point 3 is the new idea. Chapter 1's agent could fail. This one can RECOVER.
"""

from __future__ import annotations

import os
from typing import cast

from dotenv import load_dotenv
from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam

from tools import ALL_TOOLS
from typed_tool import ToolError, registry, schemas

# Circuit breaker #1, from Chapter 1: total turns.
MAX_ITERATIONS = 10

# Circuit breaker #2, new in Chapter 2: how many times may the model send
# arguments we reject before we give up on it?
#
# Some ceiling is required. Without one, a model that has decided a parameter
# exists will keep sending it, read the rejection, apologise, and send it again
# -- a polite infinite loop that costs a request every lap. Two retries is
# usually enough: the first rejection tells it WHAT is wrong, and if the second
# attempt is still invalid, more attempts rarely help.
MAX_INVALID_CALLS = 3


def run_agent(user_message: str, system_prompt: str | None = None) -> str:
    """Run the loop until the model stops calling tools, or a budget trips."""
    load_dotenv()
    client = OpenAI(
        api_key=os.environ["OPENAI_API_KEY"],
        base_url=os.environ["OPENAI_BASE_URL"],
    )
    model = os.environ.get("MODEL_NAME", "gemini-2.5-flash")

    tools_by_name = registry(ALL_TOOLS)
    tool_schemas = schemas(ALL_TOOLS)

    messages: list[ChatCompletionMessageParam] = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": user_message})

    invalid_calls = 0

    for iteration in range(1, MAX_ITERATIONS + 1):
        print(f"\n--- Iteration {iteration} ---")

        # STEP 1 -- send the conversation.
        response = client.chat.completions.create(
            model=model,
            messages=messages,
            tools=tool_schemas,
        )

        # STEP 2 -- parse. Keep the assistant turn verbatim so tool results can
        # link back to it by tool_call_id.
        assistant_message = response.choices[0].message
        messages.append(
            cast(ChatCompletionMessageParam, assistant_message.model_dump(exclude_none=True))
        )

        if not assistant_message.tool_calls:
            print("Model returned a final answer -- exiting loop.")
            return assistant_message.content or ""

        print(f"Model requested {len(assistant_message.tool_calls)} tool call(s):")

        # STEP 3 + 4 -- validate, execute, append.
        for tool_call in assistant_message.tool_calls:
            if tool_call.type != "function":
                continue

            name = tool_call.function.name
            raw = tool_call.function.arguments
            print(f"  -> {name}({raw})")

            try:
                tool = tools_by_name[name]
            except KeyError:
                invalid_calls += 1
                result = (
                    f"ERROR: there is no tool called '{name}'. "
                    f"Available tools: {', '.join(sorted(tools_by_name))}."
                )
            else:
                try:
                    # Parse, validate, dispatch. Anything wrong with the model's
                    # arguments is caught here, and the function body is never
                    # entered -- so a rejected call has NO side effects.
                    result = tool.call(raw)

                except ToolError as exc:
                    # The model's problem. Hand it back and let it try again.
                    invalid_calls += 1
                    result = str(exc)

                except Exception as exc:
                    # OUR problem: a bug in the tool, a dead file, a bad import.
                    # The model cannot fix any of that, so do not invite it to
                    # try. Say so plainly and let it report the failure.
                    print(f"     !! internal failure in {name}: {type(exc).__name__}: {exc}")
                    result = (
                        f"ERROR: the tool '{name}' failed internally. This is not "
                        f"something you can fix by changing the arguments. Tell the "
                        f"user the tool is unavailable and stop retrying it."
                    )

            print(f"     <- {result}")
            messages.append({"role": "tool", "tool_call_id": tool_call.id, "content": result})

        # Circuit breaker #2 fires here, AFTER the results are in the
        # conversation -- so the model's last rejection is still on record.
        if invalid_calls >= MAX_INVALID_CALLS:
            return (
                f"[Agent stopped: {invalid_calls} invalid tool calls. The model could "
                f"not produce arguments matching the tool contracts.]"
            )

    return f"[Agent reached max iterations ({MAX_ITERATIONS}) without completing the task.]"


if __name__ == "__main__":
    # This task is chosen to force a Literal argument and a range-constrained
    # one in the same run. Watch the tool calls: the model reads the enum out of
    # the generated schema and uses the exact strings.
    task = (
        "Convert 98.6 fahrenheit to celsius, then tell me what 15% of that "
        "number is. Finish with one clean sentence."
    )

    print(f"USER TASK:\n  {task}")
    print("=" * 72)

    final_answer = run_agent(
        user_message=task,
        system_prompt=(
            "You are a careful assistant. Use the available tools to answer the "
            "user's question step by step. If a tool rejects your arguments, read "
            "the error, fix the arguments, and try once more. Never invent values "
            "the user did not give you. When you have everything you need, stop "
            "calling tools and write a clean final summary."
        ),
    )

    print("=" * 72)
    print(f"\nFINAL ANSWER:\n{final_answer}\n")
