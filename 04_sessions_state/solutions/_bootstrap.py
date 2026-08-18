"""
Put the spine's earlier chapters on the import path.

Chapter 3 introduced this file and explained why it has to exist -- read
`../../03_structured_outputs/solutions/_bootstrap.py` first if you have not.
The short version: chapter folders are named `03_...`, which is not a valid
Python identifier, so they cannot be packages, so a script only ever sees its
own directory. Pyright's `extraPaths` fixes type checking and does nothing at
runtime.

Chapter 4 adds ONE line to Chapter 3's version -- Chapter 3's own solutions,
because `replies.py` (the output contract) is carried forward unchanged.

That is worth noticing rather than skipping past. Four chapters in, the spine's
import graph is:

    Chapter 4  expense_agent_v4   ->  Chapter 3  replies
                                 ->  Chapter 2  expense_tools, expense_store
                                 ->  Chapter 2  chapter (the @tool decorator)

Nothing was copied forward. Every chapter added a layer and left the layer
underneath alone. If a chapter ever cannot do that, the boundary it is crossing
is in the wrong place -- and that is a design signal worth listening to.
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[2]

_SPINE_PATHS = [
    _REPO_ROOT / "02_typed_tools" / "solutions",
    _REPO_ROOT / "02_typed_tools" / "from_scratch",
    _REPO_ROOT / "03_structured_outputs" / "solutions",
]

for _path in _SPINE_PATHS:
    _text = str(_path)
    if _text not in sys.path:
        sys.path.insert(0, _text)
