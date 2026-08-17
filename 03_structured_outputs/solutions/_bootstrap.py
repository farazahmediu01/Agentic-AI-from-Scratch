"""
Put Chapter 2's solutions on the import path.

WHY THIS FILE EXISTS, AND WHY IT IS SLIGHTLY UGLY
-------------------------------------------------
From this chapter on, the spine is ONE codebase rather than a fresh copy per
chapter (see "The Taper Rule" in `CLAUDE.md`). Chapter 3 therefore imports
Chapter 2's `expense_store` and `expense_tools` instead of duplicating ~400
lines of storage and tool definitions a third time.

That is the right call for a curriculum whose whole claim is "one app that
grows". It has a real cost, and here it is:

    Chapter folders are named `01_...`, `02_...`, `03_...`. Those are not valid
    Python identifiers, so they cannot be packages, so they cannot be imported.
    Every chapter runs as loose scripts, and a script only gets its OWN
    directory on `sys.path`.

`pyproject.toml` tells *pyright* where to look with `extraPaths`. Pyright is a
type checker; it does not run anything, so that setting has no effect at
runtime. The interpreter still needs telling separately, which is this file.

Import it FIRST, before any spine import:

    import _bootstrap  # noqa: F401
    import expense_store

The `_` prefix is not decoration -- it sorts before every letter in ASCII, so
ruff's import sorter keeps this line above the imports that depend on it. Delete
the underscore and the sorter will happily move it below `expense_store` and
break the file.

> **The lesson worth taking:** "just import it from the other folder" is one
> line of intent and three paragraphs of consequence. Package layout is a design
> decision, not a formality. A real project would make these installable
> packages; a teaching repo that renamed its chapters `ch01`, `ch02` would lose
> the numbered ordering everyone navigates by. We chose navigability and paid
> for it here, in one file, once.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

# Chapter 2's solutions hold the spine's storage and tools; its from_scratch
# folder holds `typed_tool.py`, which `expense_tools` imports.
_SPINE_PATHS = [
    _REPO_ROOT / "02_typed_tools" / "solutions",
    _REPO_ROOT / "02_typed_tools" / "from_scratch",
]

for _path in _SPINE_PATHS:
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)
