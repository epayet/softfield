---
id: f290-01-session-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 6
max_diff: 9000                      # a move counts its lines twice: removed and added
depends_on: []
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/session.py
  - runner/milestone.py
  - runner/requests.py
  - runner/cli.py
  - runner/bench.py
  - tests/runner/test_loop.py
  - tests/runner/conftest.py
  - tests/runner/test_milestone.py
  - tests/runner/test_backup.py
  - tests/runner/test_bench.py
  - tests/runner/test_cli.py
tests:
  - tests/runner/test_session.py
---

### Goal
What every runner job shares (the session, the clock, the job records, the queue's rows, routing and `call_claude`) lives in `runner/session.py`, with its tests in `tests/runner/test_session.py`; nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8): this is the first move, the one the others import.
- The candidates are in `runner/loop.py` from `MAIN = "main"` to the end of `def call_claude`: `class Session`, `def open_session`, `def now`, `def clock`, `class Ticker`, `def with_progress`, the in-flight helpers, `def record_start`, `def record_ticket`, the attempt records, `def enqueue`, `def park_row`, `def finish_row`, `class Parked`, the routing (`def candidates`, `def first_agent`, `def route_developer`), `def _notify`, `def set_activity`, `def doing`. Apply D3 to each: what only one job kind uses (`def give_direction`, `def _name_checkpoint`, the backup and push checks) stays in `runner/loop.py` for its own ticket; what only the scheduler uses stays.
- `close_session` uses the report: take it too if `runner/milestone.py` keeps needing it, as it does today.
- D5 matters most here: `now`, `clock`, `set_activity`, `call_claude`, `_notify` and the constants are patched by name in `tests/runner/test_loop.py`, `tests/runner/test_backup.py`, `tests/runner/test_bench.py`, `tests/runner/test_cli.py` and `tests/runner/test_milestone.py`; after the move those patches target `session`, and `runner/loop.py` calls them as `session.now()`.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`, as f143-03 did (`.softfield/tasks/done/f143-03-thread-page-own-module.md`); check with `git diff --stat`.
- Then D7: Grep `.softfield/tasks/ready/`, `.softfield/tasks/later/`, `.softfield/developer.md`, `AGENTS.md` and `runner/instructions/` for each moved name beside `runner/loop.py`, and point them at `runner/session.py`.

### Done when
- `runner/session.py` holds the session and what two or more job kinds share, at most 1,800 lines, and imports nothing from `runner/loop.py`
- the moved tests pass in `tests/runner/test_session.py`, none renamed or edited beyond imports and patch targets, and every test left in `tests/runner/` passes unchanged otherwise
- `runner/cli.py`, `runner/milestone.py`, `runner/requests.py` and `runner/bench.py` import the moved names from `runner/session.py`
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included
