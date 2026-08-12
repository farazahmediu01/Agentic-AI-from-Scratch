"""
One import shim, explained once, so the rest of `solutions/` stays clean.

The machinery you built lives in `../from_scratch/typed_tool.py`. These solution
scripts are run directly (`uv run python .../check_expenses.py`), which puts
only THIS folder on `sys.path` — so the sibling folder is invisible without help.

Every solution file imports from here instead:

    from chapter import Tool, ToolError, tool

Two things worth taking from this file, both larger than the six lines of code:

  1. This is what a package would do for you. `shared/models.py` at the repo
     root needs no shim, because `pyproject.toml` installs `shared` as a real
     package. Chapter folders cannot be packages — `02_typed_tools` starts with
     a digit, so it is not a valid Python identifier. Script-style folders are a
     deliberate teaching choice, and this is the tax they charge.

  2. When you do reach for a shim, put it in ONE file. A `sys.path` line copied
     into eight scripts is eight places to be wrong, and the failure mode is an
     import that works from one directory and not another.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "from_scratch"))

from typed_tool import Tool, ToolError, explain, registry, schemas, tool

__all__ = ["Tool", "ToolError", "explain", "registry", "schemas", "tool"]
