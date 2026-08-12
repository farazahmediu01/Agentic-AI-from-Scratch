"""
Chapter 2 — the machinery. This file is the chapter.

Everything else in `from_scratch/` either shows why this file is needed
(`break_it.py`, `handrolled.py`) or uses it (`tools.py`, `agent.py`).

What it gives you:

    @tool                 turn a plain function into a validated, self-describing Tool
    Tool.schema           the JSON Schema, GENERATED from the signature
    Tool.call(raw_json)   parse -> validate -> dispatch, with model-readable failures
    ToolError             a failure the MODEL is meant to read and recover from

Read `tool()` first. It is 30 lines, and those 30 lines are the honest core of
what `@function_tool` does in the OpenAI Agents SDK.
"""

from __future__ import annotations

import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any, cast, get_type_hints

from openai.types.chat import ChatCompletionToolParam
from pydantic import BaseModel, ConfigDict, ValidationError, create_model


class ToolError(Exception):
    """
    A failure the model is expected to read and act on.

    This is the distinction Chapter 1 did not make. There are two kinds of
    failure inside an agent and they belong to different owners:

      ToolError  -> the MODEL's problem. Bad arguments, unknown tool, a business
                    rule it violated. The text goes back into the conversation
                    and the model gets another attempt.
      everything -> OUR problem. A 429, a dead database, a bug in our code. The
      else        model cannot fix any of those, so handing them to it just
                  burns turns while it invents workarounds.

    Ask of every error you raise: *can the model do something about this?*
    """


@dataclass(frozen=True)
class Tool:
    """A callable the model is permitted to invoke, plus the contract it must obey."""

    name: str
    description: str
    args_model: type[BaseModel]
    fn: Callable[..., Any]
    schema: ChatCompletionToolParam

    @property
    def parameters(self) -> dict[str, Any]:
        """
        The generated JSON Schema for this tool's arguments.

        A convenience, and a testing surface. `test_expense_tools.py` asserts on
        what comes out of here -- because a tool can behave perfectly and still
        be broken, if the contract it published to the model was wrong.
        """
        return cast(dict[str, Any], self.schema["function"].get("parameters", {}))

    def call(self, raw_arguments: str) -> str:
        """
        Run one tool call, start to finish.

        Four stages, and the order is the whole point — nothing reaches your
        function body until every stage above it has passed:

            1. PARSE     the JSON string the model emitted
            2. VALIDATE  it against the args model
            3. DISPATCH  into the real function
            4. SERIALISE the result back to a string for the conversation
        """
        # 1. PARSE. Tool arguments arrive as a STRING of JSON, not a dict.
        #    Models do emit malformed JSON — truncated, trailing commas, prose.
        try:
            payload = json.loads(raw_arguments) if raw_arguments.strip() else {}
        except json.JSONDecodeError as exc:
            raise ToolError(
                f"The arguments you sent to '{self.name}' were not valid JSON "
                f"({exc.msg} at position {exc.pos}). Send the arguments again as a "
                f"single valid JSON object."
            ) from exc

        if not isinstance(payload, dict):
            raise ToolError(
                f"The arguments for '{self.name}' must be a JSON object like "
                f'{{"key": "value"}}, but you sent {type(payload).__name__}.'
            )

        # 2. VALIDATE. This is the line that separates Chapter 2 from Chapter 1.
        #    One call replaces every isinstance() check you would write by hand,
        #    and it fails BEFORE the function body runs — so a bad call cannot
        #    half-execute and leave the world in a weird state.
        try:
            args = self.args_model.model_validate(payload)
        except ValidationError as exc:
            raise ToolError(explain(self.name, exc)) from exc

        # 3. DISPATCH. By here, every argument is present, correctly typed, and
        #    inside its allowed range. The function body can stop defending itself.
        result = self.fn(**args.model_dump())

        # 4. SERIALISE. The conversation is a list of strings; the model cannot
        #    read a Python float.
        return result if isinstance(result, str) else json.dumps(result)


def explain(tool_name: str, exc: ValidationError) -> str:
    """
    Turn Pydantic's error list into a message a MODEL can act on.

    Compare the two audiences:

      For a developer:  "1 validation error for LogExpenseArgs
                         amount: Input should be a valid number"
      For a model:      "INVALID ARGUMENTS for 'log_expense'. Nothing was
                         executed. amount: input should be a valid number
                         (you sent 'fifty'). Fix and call again."

    Same facts. The second one names the tool, states that nothing happened,
    echoes what was actually sent, and says what to do next. Error messages
    inside an agent are not diagnostics — they are instructions.
    """
    lines: list[str] = []
    for err in exc.errors():
        field = ".".join(str(part) for part in err["loc"]) or "(whole object)"
        # `err["msg"]` goes through UNCHANGED, deliberately. An earlier version of
        # this function lowercased it so the bullet list would read tidily -- and
        # in doing so it rewrote the enum values quoted inside the message, so an
        # invalid category came back as "should be 'food & dining'". The model
        # then dutifully sent the lowercased string and was rejected again.
        # Never reformat text that quotes values the reader is meant to copy.
        lines.append(f"  - {field}: {err['msg']} (you sent: {err.get('input')!r})")

    return (
        f"INVALID ARGUMENTS for tool '{tool_name}'. Nothing was executed.\n"
        + "\n".join(lines)
        + f"\nFix the arguments and call '{tool_name}' again. If the correct value is "
        f"something the user never told you, ask them for it. Do not invent it."
    )


# Pydantic's constraint names are not always JSON Schema's. Usually it
# translates them for you -- but when a field carries a custom validator,
# Pydantic can no longer prove what the accepted input looks like, and it falls
# back to emitting the raw constraint key instead.
#
# The failure is silent and one-directional: `"gt": 0` is not a JSON Schema
# keyword, so the model never learns the value must be positive. Your validation
# still rejects the bad call, so nothing crashes -- you simply pay an extra
# round trip for a rule you thought you had published.
#
# This is the schema-generation equivalent of a typo, and the reason
# `test_expense_tools.py` asserts on the SCHEMA and not only on the behaviour.
_JSON_SCHEMA_NAMES = {
    "gt": "exclusiveMinimum",
    "ge": "minimum",
    "lt": "exclusiveMaximum",
    "le": "maximum",
    "multiple_of": "multipleOf",
    "min_length": "minLength",
    "max_length": "maxLength",
}


def _clean_schema(schema: dict[str, Any]) -> dict[str, Any]:
    """
    Make Pydantic's output fit to send: drop noise, fix constraint names.

    Dropping "title" is the cosmetic half. Every key here is sent to the model
    on EVERY turn of EVERY run, and `"title": "Amount"` sitting above
    `"description": "Amount in PKR"` is a recurring token cost that teaches the
    model nothing.

    Renaming the constraints is the half that changes behaviour.
    """
    schema.pop("title", None)
    for prop in schema.get("properties", {}).values():
        if not isinstance(prop, dict):
            continue
        prop.pop("title", None)
        for pydantic_name, json_schema_name in _JSON_SCHEMA_NAMES.items():
            if pydantic_name in prop:
                prop[json_schema_name] = prop.pop(pydantic_name)
    return schema


def tool(fn: Callable[..., Any]) -> Tool:
    """
    Turn a plain typed function into a Tool.

    Read this as three moves:

      1. Read the signature      -> what arguments exist, which are required
      2. Build a validator       -> a Pydantic model with one field per argument
      3. Publish the contract    -> JSON Schema generated from that same model

    Move 3 is the one worth sitting with. In Chapter 1 the schema and the
    function were two separate artefacts kept in sync by hand, which means they
    drift the first time someone edits one and forgets the other. Here there is
    only one source of truth — the signature — and both the validator and the
    schema are derived from it. They cannot disagree.

    This is also why type hints stop being documentation in agentic Python.
    `amount: float` is not a note to the next developer. It is executable: it
    becomes `"type": "number"` in the contract the model reads, and a runtime
    check on the way back in.
    """
    signature = inspect.signature(fn)
    hints = get_type_hints(fn, include_extras=True)

    # A field per parameter: (type, default). `...` means required.
    fields: dict[str, Any] = {}
    for name, param in signature.parameters.items():
        annotation = hints.get(name, Any)
        default = ... if param.default is inspect.Parameter.empty else param.default
        fields[name] = (annotation, default)

    args_model: type[BaseModel] = create_model(
        f"{fn.__name__.title().replace('_', '')}Args",
        # extra="forbid" is a deliberate, opinionated choice. The default would
        # silently ignore arguments the model invented. We would rather the model
        # be TOLD it hallucinated a parameter than have it quietly believe the
        # call did something it did not.
        __config__=ConfigDict(extra="forbid"),
        **fields,
    )

    description = inspect.getdoc(fn) or ""
    if not description:
        raise ValueError(
            f"Tool '{fn.__name__}' has no docstring. The docstring IS the "
            f"description the model reads to decide whether to call this tool."
        )

    schema: ChatCompletionToolParam = {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": description,
            "parameters": _clean_schema(args_model.model_json_schema()),
        },
    }

    return Tool(
        name=fn.__name__,
        description=description,
        args_model=args_model,
        fn=fn,
        schema=schema,
    )


def registry(tools: list[Tool]) -> dict[str, Tool]:
    """Name -> Tool, so the loop can look up whatever the model asked for."""
    return {t.name: t for t in tools}


def schemas(tools: list[Tool]) -> list[ChatCompletionToolParam]:
    """The `tools=` payload for the API. Generated, never hand-written again."""
    return [t.schema for t in tools]
