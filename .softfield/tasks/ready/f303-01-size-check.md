---
id: f303-01-size-check
milestone: f303-from-a-factory-suggestion-add-a
difficulty: 3
depends_on: []
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
Add a `size` check, in check-all and the gates, that fails when a Python file in the repo has more lines than the project allows (ADR 55 items 1–3 and 9).

## Context
- `.softfield/adr/55-a-file-at-its-size-limit-is-split-by-plan.md` and Decisions D1–D2 in `.softfield/cards/f303-from-a-factory-suggestion-add-a.md`: the settings, the problem lines, the names. Every line counts, comments and blank lines too.
- `runner/config.py`: `Checks` and `project_checks` read `[checks]`; add `max_lines`, `max_test_lines` (default 0, no check) and `over_limit` (default empty) the way `layouts` and `test_dirs` are read.
- `runner/gates.py`: `layout_problems` and `gate_layout` are the example for `size_problems` and its gate; add the gate to `GATES` right after `gate_layout`, and a line to `HINTS`: "Don't split, trim or move code to get under the limit: the runner blocks the ticket and the lead plans the split."
- `runner/checks.py`: `check_all` runs `layout` as a `_problems` check; add `size` after it.
- `.softfield/project.toml`: set Softfield's limits and `over_limit` as D1 says, with a one-line comment naming ADR 55.
- `docs/workflow.md`: the numbered gate list (item 6 is `layout`) gets `size` after it, one line.
- List the files with `git ls-files`, so `.venv` and untracked files are never read.

## Done when
- with no limits set, `size_problems` returns nothing on any repo
- a code file one line over `max_lines` is a problem; one at the limit isn't; comment and blank lines count
- a file under a `test_dirs` folder is held to `max_test_lines`, not `max_lines`
- a file in `dependency_dirs` is never counted
- a file in `over_limit` that is over is no problem; one that is under its limit is, with the "remove it from over_limit" line
- `softfield check-all` on Softfield's main passes with the settings in `.softfield/project.toml` (the five listed files are the only ones over)
- the listed `tests:` pass, and fail without the change
- all gates pass
