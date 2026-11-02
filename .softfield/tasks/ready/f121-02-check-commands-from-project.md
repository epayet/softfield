---
id: f121-02-check-commands-from-project
milestone: f121-projects-not-on-main-or-not
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/config.py
  - runner/checks.py
  - runner/gates.py
  - runner/loop.py
  - runner/templates/project.toml
  - factory_dashboard/static/factory.js
tests:
  - tests/runner/test_config.py
  - tests/runner/test_checks.py
  - tests/runner/test_gates.py
---

### Goal
`check-all`, the gates and the auto-format before them run the project's own lint, fix and test commands from `[checks]`, with today's ruff and pytest commands as the defaults.

### Context
Read D2 and D3 in `.softfield/cards/f121-projects-not-on-main-or-not.md`, then `Checks`, `project_checks` and `suite_args` in `runner/config.py`, `check_all` in `runner/checks.py`, and `autoformat`, `gate_ruff`, `gate_task_tests`, `gate_all_tests`, `HINTS` and `GATES` in `runner/gates.py`, and `MECHANICAL` in `runner/loop.py`.
- New keys in `Checks`: `lint`, `fix`, `test`, `fix_suffixes`, each defaulting to the exact argv D2 gives, so Softfield, Coucou and travel-companion run what they run today. A key of the wrong shape raises `ConfigError`, as the others do.
- `fix` commands are ended by the runner: with the changed files whose suffix is in `fix_suffixes` (auto-format before the gates), or with `.` (`check-all --fix`). The fixes run in their order; a non-zero exit is not a failure, as today.
- The ticket's tests or `suite_args` end the `test` command; `-n` workers only when `test_workers` is above 0, as today.
- "ruff check" and "ruff format" become one check, `lint`, in check-all; the gate `ruff` becomes `lint`, in `GATES`, `HINTS` and `MECHANICAL`. The hint names the project's fix commands, not ruff. Find every other place a check or gate is named "ruff" in `runner/` and rename it. The drawing's label "ruff · mypy" in `factory_dashboard/static/factory.js` becomes "lint · mypy".
- Add commented examples of `lint`, `fix`, `test` and `fix_suffixes` to `runner/templates/project.toml`, the defaults first, a JavaScript one beside them (D2's card notes).

### Done when
- with no new keys, check-all, the gates and the auto-format run exactly today's commands (a test asserts the argv)
- a project with `lint = [["sh", "-c", "exit 1"]]` fails check-all's `lint` and the `lint` gate, whatever ruff would say
- a project's `test` command gets the ticket's tests appended for `task-tests`, and its suite for `all-tests` and check-all
- the auto-format runs the project's `fix` commands on changed files with a listed suffix only, and on none when no file has one
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
