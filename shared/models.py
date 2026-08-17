"""
The model factory — one seam, two providers.

WHY THIS FILE EXISTS
--------------------
The OpenAI Agents SDK defaults to the **Responses API** when you hand it a bare
model name like `Agent(model="gpt-4o")`. This curriculum deliberately runs on
the **Chat Completions API** against Gemini's OpenAI-compatible endpoint, because:

  * it is free, so nobody is billed for learning, and
  * Chat Completions is *stateless* — every byte the model sees lives in a list
    you own. The state chapters (sessions, and the context window) are
    unteachable on server-side state, because there would be nothing in your
    process to prune.

See `../RESPONSES_VS_CHATCOMPLETIONS.md` for the full comparison.

That decision is correct for nearly every chapter, and wrong for the late one on
hosted tools (web search, file search, code interpreter), which only exist on
the Responses API. Rather than refactor every chapter when we get there, we put
the switch in one place now and flip an environment variable later.

    AGENT_PROVIDER=gemini   -> OpenAIChatCompletionsModel   (default, free)
    AGENT_PROVIDER=openai   -> OpenAIResponsesModel         (paid, hosted tools)

SCOPE — read this before you import it
--------------------------------------
This factory is for `with_sdk/` code ONLY.

`from_scratch/` chapters keep building their client inline with an explicit
`OpenAI(api_key=..., base_url=...)`. Hiding that construction behind a helper
would defeat the entire point of the from-scratch layer: seeing the wire.

Try it:  uv run python -m shared.models
"""

from __future__ import annotations

import os
from typing import Literal, get_args

from agents import (
    Model,
    OpenAIChatCompletionsModel,
    OpenAIResponsesModel,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

Provider = Literal["gemini", "openai"]

DEFAULT_PROVIDER: Provider = "gemini"
GEMINI_OPENAI_ENDPOINT = "https://generativelanguage.googleapis.com/v1beta/openai/"
DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"
DEFAULT_OPENAI_MODEL = "gpt-4o"

__all__ = ["Provider", "active_provider", "make_model"]


def active_provider() -> Provider:
    """
    Which provider the environment currently selects.

    Reads `AGENT_PROVIDER`, defaulting to the free path. Raises on an unknown
    value rather than silently falling back — a typo'd provider name should not
    quietly bill you, or quietly stop billing you.
    """
    load_dotenv()
    raw = os.environ.get("AGENT_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    valid = get_args(Provider)
    if raw not in valid:
        raise ValueError(
            f"AGENT_PROVIDER={raw!r} is not recognised. Valid values: {', '.join(valid)}."
        )
    return raw  # type: ignore[return-value]


def _require(name: str, hint: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Environment variable {name} is not set.\n  {hint}")
    return value


def _gemini_model() -> Model:
    """
    Chat Completions against Gemini's OpenAI-compatible endpoint.

    `OPENAI_API_KEY` / `OPENAI_BASE_URL` are the variable names Chapter 1 already
    uses, kept so existing `.env` files and every `from_scratch/` script keep
    working unchanged.
    """
    client = AsyncOpenAI(
        api_key=_require(
            "OPENAI_API_KEY",
            "Get a free Gemini key at https://aistudio.google.com/apikey and put it in .env",
        ),
        base_url=os.environ.get("OPENAI_BASE_URL", "").strip() or GEMINI_OPENAI_ENDPOINT,
    )

    # The SDK's hosted trace viewer authenticates against api.openai.com. With a
    # Gemini key there is nothing to authenticate, so every run would emit an
    # export error. We turn tracing on properly in the observability chapter.
    set_tracing_disabled(True)

    return OpenAIChatCompletionsModel(
        model=os.environ.get("MODEL_NAME", "").strip() or DEFAULT_GEMINI_MODEL,
        openai_client=client,
    )


def _openai_model() -> Model:
    """
    The Responses API against real OpenAI. Costs money. Used only by the hosted-tools
    chapter, and by anyone who wants to see the difference for themselves.

    Deliberately a DIFFERENT key variable from the Gemini path. If both reused
    `OPENAI_API_KEY`, flipping AGENT_PROVIDER would send a Gemini key to
    api.openai.com and fail with a confusing 401.
    """
    client = AsyncOpenAI(
        api_key=_require(
            "OPENAI_PLATFORM_API_KEY",
            "This is a real, paid OpenAI key from https://platform.openai.com/api-keys "
            "- not your Gemini key.",
        )
    )
    return OpenAIResponsesModel(
        model=os.environ.get("OPENAI_MODEL", "").strip() or DEFAULT_OPENAI_MODEL,
        openai_client=client,
    )


def make_model(provider: Provider | None = None) -> Model:
    """
    Build the `Model` object to hand to `Agent(model=...)`.

    Args:
        provider: Override the environment. Leave as None in chapter code so a
            single `AGENT_PROVIDER` change switches the whole curriculum.

    Returns:
        An `OpenAIChatCompletionsModel` (gemini) or `OpenAIResponsesModel` (openai).

    Example:
        agent = Agent(name="...", instructions="...", model=make_model(), tools=[...])
    """
    load_dotenv()
    chosen = provider or active_provider()
    return _gemini_model() if chosen == "gemini" else _openai_model()


if __name__ == "__main__":
    # A diagnostic, not a demo: prints which provider and model you are wired to
    # WITHOUT spending a token. Run it first when a chapter behaves oddly.
    model = make_model()
    provider = active_provider()
    api = "Responses" if provider == "openai" else "Chat Completions"
    print(f"AGENT_PROVIDER : {provider}")
    print(f"wire format    : {api} API")
    print(f"model class    : {type(model).__name__}")
    print(f"model name     : {getattr(model, 'model', '?')}")
    print(f"hosted tools   : {'available' if provider == 'openai' else 'UNAVAILABLE on this path'}")
