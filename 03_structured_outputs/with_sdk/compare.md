# Chapter 3 — our spike vs the SDK, line by line

> `from_scratch/prompt_and_parse.py` → `Agent(output_type=...)`

## The map

| We wrote | SDK | What it does for us |
|---|---|---|
| `JSON_PROMPT` — 11 lines describing the keys and begging for no fences | *(nothing)* | The schema **is** the description. Nothing to write, nothing to drift |
| `json.loads(raw)` | handled | Parsing |
| `_FENCE`, `_FIRST_OBJECT`, `_TRAILING_COMMA` | *(unnecessary)* | The provider is constrained at sampling time, so there are no fences to strip |
| `ExpenseReply.model_validate(parsed)` | handled | Validation, before `final_output` exists |
| a retry loop we sketched and did not enjoy | handled | Retry on a malformed response |
| *(we could not build it)* | `"strict": true` | **Constrained decoding in the model server.** Not a layer we can reach |
| `dict[str, Any]` at the call site | `ExpenseReply` | A typed object — `pyright` checks the field names you read |

## The one number worth remembering

| | passed |
|---|---|
| `json.loads` on 8 real responses | **3/8** |
| after fence-stripping + regex + comma repair | 7/8 |
| after validation | 6/8 |
| `output_type=` | shape guaranteed, or an exception |

The middle two rows are the trap. A tolerant parser looks like progress — it took 3/8 to 7/8 — and it bought back **only** the responses that were wrapped wrong. Every response that was *shaped* wrong survived it untouched, because a missing key is not a punctuation problem.

## What does NOT transfer

**A shape is not a fact.** `output_type=` guarantees `remaining` is a float. It guarantees nothing about whether that float matches what `subtract` returned. This is Chapter 2's §7b lesson one level up, and the check still has to live outside the model. See README §8.

**Exactly-one-of is not expressible.** A four-optional-field union satisfies its schema when zero fields are set and when two are. JSON Schema cannot portably say otherwise, so `replies.py` enforces it with a `model_validator` that runs after the model has spoken. That is your first guardrail; Chapter 8 names it.

**A union is not free.** Every branch you add is a decision the model has to make correctly, and branch selection is a judgement — so it stays partly in the prompt. Adding an outcome means touching a type **and** a prompt, which is why Practice 7 makes you do both.

**Retry budgets are yours.** The SDK retries a malformed response, but the free-tier 429 that will actually stop your demo is not a malformed response. `expense_agent_v3.py` re-adds the backoff Chapter 1's `loop.py` had — worth noticing as a general shape: **when you adopt a framework, the things you built that it does not provide do not announce themselves on the way out.** They are simply gone, and you find out during the first noisy demo.

## Portability note

`output_type=Logged | NeedMoreInfo` (a bare union) works, but puts an `anyOf` at the top level of a strict schema, and providers differ on that. One wrapper model with optional branch fields is the portable spelling and survives the `AGENT_PROVIDER` swap unchanged. That is the shape `replies.py` uses, and the reason is in its docstring rather than left as folklore.
