---
id: f303-04-imports-at-top
milestone: f303-from-a-factory-suggestion-add-a
difficulty: 4
depends_on: [f303-01-size-check]
files:
  - runner/config.py
  - runner/gates.py
  - runner/checks.py
  - .softfield/project.toml
  - docs/workflow.md
tests:
  - tests/runner/test_config.py
  - tests/runner/test_gates.py
  - tests/runner/test_checks.py
agent: lead
area: factory
---

## Goal
Add an `imports` check, in check-all and the gates, that fails when a file imports the project's own modules inside a function more often than the project allows, so no new hidden import cycle comes in (ADR 55 items 4 and 5).

## Context
- `.softfield/adr/55-a-file-at-its-size-limit-is-split-by-plan.md` items 4–5 and Decisions D3–D4 in `.softfield/cards/f303-from-a-factory-suggestion-add-a.md`: the settings, what counts, the problem lines, the name.
- `runner/config.py`: add `imports_at_top` and `imports_in_functions` to `Checks` and `project_checks`, as f303-01 added the size settings.
- `runner/gates.py`: `size_problems` (from f303-01) is the example for `import_problems` and its gate, after `size` in `GATES`, with a `HINTS` line: "Don't move or copy code to avoid the import: the runner blocks the ticket and the lead plans the move."
- `runner/checks.py`: add `imports` after `size` in `check_all`.
- What counts: `from runner.milestone import card` inside a `def` does; `from fastapi.testclient import TestClient` inside one doesn't (not the project's own); the block under `if TYPE_CHECKING:` at the top of `factory_dashboard/overview.py` doesn't.
- `.softfield/project.toml`: turn it on and fill `[checks.imports_in_functions]` with each file's count on main as the check finds it (about 60 in `runner/` and `factory_dashboard/`), with a one-line comment naming ADR 55 item 5.
- `docs/workflow.md`: the gate list gets `imports` after `size`, one line.

## Done when
- with `imports_at_top` off, `import_problems` returns nothing
- an own-module import inside a function, a method or a nested `if` in a function counts; one at the top level, under `if TYPE_CHECKING:`, or of another package doesn't
- a file with more than its allowance (0 when unlisted) is a problem naming each such line; a file with fewer is a problem asking to lower its allowance; a file at its allowance isn't
- `softfield check-all` on Softfield's main passes with the settings in `.softfield/project.toml`
- the listed `tests:` pass, and fail without the change
- all gates pass
