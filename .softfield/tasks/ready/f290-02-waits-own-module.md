---
id: f290-02-waits-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 5
max_diff: 6000                      # a move counts its lines twice: removed and added
depends_on: [f290-01-session-own-module]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/waits.py
  - runner/session.py
  - runner/milestone.py
  - runner/requests.py
  - runner/cli.py
  - tests/runner/test_loop.py
  - tests/runner/conftest.py
  - tests/runner/test_milestone.py
tests:
  - tests/runner/test_waits.py
---

### Goal
How the runner waits on Claude's limits (the reserve switches, the windows and readings, the login check, the hold, parking support jobs, passing over and waiting for room) lives in `runner/waits.py`, with its tests in `tests/runner/test_waits.py`; nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8), and f290-01's commit (`git log -1 --stat`), which moved the shared base to `runner/session.py`: follow it.
- The candidates in `runner/loop.py`: from `def _switch_ends` to the end of `def park_review` (`def switch_on`, `def set_switch`, `def lapse_switches`, the windows, `def fresh_reading`, the login items, `def check_login`, `class Hold`, `def claude_hold`, `def _park_support`), plus `def wait_for_claude`, `def agent_windows`, `def wait_for_room`, the switch takers (`def _take_switches` and the `_week_switched_on` family), `def _passing_over`, `def _passed_over`, `def _held_at_the_limit` and `def _wait_for_reset`. Apply D3: a helper only the scheduler uses (the idle line) stays.
- The switches' constants go with them (`SWITCHES`, `WEEK`, `FIVE_HOUR`, `FIVE_HOUR_KIND`, `RESERVE_KIND`). `runner/requests.py` reads those as `loop.X` and calls `loop.set_switch`, `loop.lapse_switches`; `runner/milestone.py` imports `park_review`, `_passed_over`, `_windows_now`, `wait_for_room`: point them at `runner/waits.py` (D4).
- D5: `fresh_reading`, `_windows_now`, `_passed_over`, `_held_at_the_limit` and `wait_for_room` are patched in `tests/runner/test_loop.py` and `tests/runner/test_milestone.py`; reach them as `waits.x()` and patch them on `waits`.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D7 for each moved name.

### Done when
- `runner/waits.py` holds Claude's holds and limits, at most 1,800 lines, and imports only `runner/session.py` of the split modules
- the moved tests pass in `tests/runner/test_waits.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included
