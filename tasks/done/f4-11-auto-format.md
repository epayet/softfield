---
id: f4-11-auto-format
milestone: f4-always-on
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/loop.py
  - runner/gates.py
tests:
  - tests/runner/test_loop.py
---

### Goal
After a developer attempt and before its gates, the runner formats and autofixes the Python files the branch changed, so no attempt is lost to formatting alone.

### Context
Read `docs/adr/17-always-on-factory.md` item 2, `runner/loop.py` (the attempt loop around `run_gates`), `runner/gates.py` (the ruff gate and its hint) and `runner/checks.py` (what `check-all --fix` runs). Test-first.
- **Why:** gpt-oss-120b lost f2-06's five attempts on ruff alone: `F401` unused import, `E501` long lines in `tests/factory_dashboard/conftest.py` (see `var/runs/20261002-151301/f2-06-overview-allowances/gates-2.txt`). `ruff format` and `ruff check --fix` would have fixed most of it.
- Run `uv run ruff format <files>` then `uv run ruff check --fix <files>` on the `.py` files the branch changed against main. Commit the result into the attempt only if something changed, with the developer's trailers. A non-zero exit from either is not a failure: the gates judge what's left.
- Developer attempts only, for every developer agent. Not lead tickets or escalations, which run `check-all` themselves.

### Done when
- an attempt whose only problem is a long line in a changed file passes the gates
- an attempt with an undefined name still fails ruff
- files the branch didn't change are never touched
- `uv run runner check-all --task f4-11-auto-format` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
