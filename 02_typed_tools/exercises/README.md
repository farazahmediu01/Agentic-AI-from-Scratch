# Your workspace

Put your work from `EXERCISES.md` here — `my_tool.py`, `unit_tools.py`, `test_adversarial.py`, `transfer_budget.py`.

This folder is already wired into the quality gate: it has its own `[[tool.pyright.executionEnvironments]]` block and is listed in `[tool.ruff] src`, so sibling-name imports (`from my_tool import tool`) resolve the same way they do in `from_scratch/`.

Which means the gate applies to your code too:

```powershell
uv run ruff format .
uv run ruff check .
uv run pyright
uv run pytest
```

`test_*.py` files you add here are collected automatically. Nothing else is.

> Do not put solutions here that you copied from `solutions/`. The folder is for what you built.
