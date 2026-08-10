"""
Chapter 1 Project solution — tools for the Freelance Invoice Agent.

Two things to study here beyond the arithmetic:

1. **Error messages are prompts.** Every `raise` below is written for the MODEL
   to read and act on, not for a developer reading a stack trace. Compare
   "KeyError: 'welding'" with the message in `lookup_rate` — one dead-ends,
   the other tells the model exactly what to say to the user.

2. **`save_invoice` has a side effect.** It is the only tool here that changes
   the world. That asymmetry is why Exercise 7's approval gate exists.
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Callable

from openai.types.chat import ChatCompletionToolParam

RATE_CARD: dict[str, float] = {
    "backend": 6500.0,
    "frontend": 6000.0,
    "ui design": 5500.0,
    "devops": 7000.0,
    "consulting": 9000.0,
}

INVOICE_DIR = Path(__file__).parent / "invoices"


# -----------------------------------------------------------------------------
# Tool implementations
# -----------------------------------------------------------------------------


def get_current_time() -> str:
    """Return the current local time as an ISO 8601 string (seconds precision)."""
    return datetime.now().isoformat(timespec="seconds")


def lookup_rate(role: str) -> float:
    """Look up the hourly rate for a role. Raises with the valid roles listed."""
    key = role.strip().lower()
    if key not in RATE_CARD:
        raise ValueError(
            f"No rate exists for role '{role}'. Tell the user this role is not on the "
            f"rate card and ask them to pick one of: {', '.join(sorted(RATE_CARD))}. "
            f"Do not invent a rate."
        )
    return RATE_CARD[key]


def line_total(hours: float, rate: float) -> float:
    """Multiply hours by an hourly rate to get one invoice line total."""
    if hours < 0:
        raise ValueError(
            f"Hours cannot be negative (got {hours}). Ask the user to confirm the "
            f"correct number of hours worked."
        )
    if rate <= 0:
        raise ValueError(f"Rate must be positive (got {rate}).")
    return hours * rate


def add(a: float, b: float) -> float:
    """Add two amounts together, e.g. to combine invoice line totals."""
    return a + b


def apply_discount(amount: float, percent: float) -> float:
    """Return the amount remaining after subtracting a percentage discount."""
    if not 0 <= percent <= 100:
        raise ValueError(f"Discount percent must be between 0 and 100 (got {percent}).")
    return amount * (1 - percent / 100)


def apply_tax(amount: float, percent: float) -> float:
    """Return the amount after adding a percentage tax."""
    if not 0 <= percent <= 100:
        raise ValueError(f"Tax percent must be between 0 and 100 (got {percent}).")
    return amount * (1 + percent / 100)


def save_invoice(
    client: str,
    lines: str,
    subtotal: float,
    discount: float,
    tax: float,
    total: float,
) -> str:
    """Write the invoice to a text file and return the saved path."""
    if not client.strip():
        raise ValueError("Client name is required. Ask the user who the invoice is for.")

    INVOICE_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    invoice_id = f"INV-{stamp}"
    path = INVOICE_DIR / f"{invoice_id}.txt"

    body = (
        f"INVOICE {invoice_id}\n"
        f"Date   : {datetime.now().isoformat(timespec='seconds')}\n"
        f"Client : {client}\n"
        f"{'-' * 52}\n"
        f"{lines}\n"
        f"{'-' * 52}\n"
        f"{'Subtotal':<24}PKR {subtotal:>14,.2f}\n"
        f"{'Discount':<24}PKR {-discount:>14,.2f}\n"
        f"{'Tax':<24}PKR {tax:>14,.2f}\n"
        f"{'TOTAL':<24}PKR {total:>14,.2f}\n"
    )
    path.write_text(body, encoding="utf-8")
    return f"Invoice saved to {path} (id {invoice_id})"


# -----------------------------------------------------------------------------
# Registry + schemas
# -----------------------------------------------------------------------------

TOOL_REGISTRY: dict[str, Callable] = {
    "get_current_time": get_current_time,
    "lookup_rate": lookup_rate,
    "line_total": line_total,
    "add": add,
    "apply_discount": apply_discount,
    "apply_tax": apply_tax,
    "save_invoice": save_invoice,
}


TOOL_SCHEMAS: list[ChatCompletionToolParam] = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "Get the current local date and time as an ISO 8601 timestamp. Takes no arguments.",
            "parameters": {"type": "object", "properties": {}, "required": []},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup_rate",
            "description": (
                "Look up the hourly billing rate in PKR for a work role. Valid roles are: "
                "backend, frontend, ui design, devops, consulting. Call this once per "
                "distinct role on the invoice before calculating any line total."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "role": {
                        "type": "string",
                        "description": "The work role, e.g. 'backend' or 'ui design'",
                    },
                },
                "required": ["role"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "line_total",
            "description": (
                "Calculate one invoice line total by multiplying hours worked by the "
                "hourly rate returned from lookup_rate."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "hours": {"type": "number", "description": "Hours worked for this role"},
                    "rate": {"type": "number", "description": "Hourly rate from lookup_rate"},
                },
                "required": ["hours", "rate"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "add",
            "description": "Add two amounts together. Use it to combine line totals into a subtotal.",
            "parameters": {
                "type": "object",
                "properties": {
                    "a": {"type": "number", "description": "First amount"},
                    "b": {"type": "number", "description": "Second amount"},
                },
                "required": ["a", "b"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_discount",
            "description": (
                "Apply a percentage discount to an amount and return the reduced amount. "
                "Apply the discount to the subtotal BEFORE tax."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount before discount"},
                    "percent": {"type": "number", "description": "Discount percentage, 0-100"},
                },
                "required": ["amount", "percent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "apply_tax",
            "description": (
                "Add a percentage tax to an amount and return the increased amount. "
                "Apply tax AFTER any discount has been applied."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "amount": {"type": "number", "description": "Amount before tax"},
                    "percent": {"type": "number", "description": "Tax percentage, 0-100"},
                },
                "required": ["amount", "percent"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "save_invoice",
            "description": (
                "Write the finished invoice to a text file and return its path. Call this "
                "ONLY after every amount has been calculated with the other tools, and only "
                "when the client name is known."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "client": {"type": "string", "description": "Client name"},
                    "lines": {
                        "type": "string",
                        "description": (
                            "The itemised lines, one per row, e.g. "
                            "'backend  12.0h x 6500.00 = 78000.00'"
                        ),
                    },
                    "subtotal": {"type": "number", "description": "Sum of all line totals"},
                    "discount": {
                        "type": "number",
                        "description": "Discount AMOUNT deducted (not the percentage)",
                    },
                    "tax": {
                        "type": "number",
                        "description": "Tax AMOUNT added (not the percentage)",
                    },
                    "total": {"type": "number", "description": "Final amount payable"},
                },
                "required": ["client", "lines", "subtotal", "discount", "tax", "total"],
            },
        },
    },
]
