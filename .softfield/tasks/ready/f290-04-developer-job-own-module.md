---
id: f290-04-developer-job-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 5
max_diff: 7000                      # a move counts its lines twice: removed and added
depends_on: [f290-03-replan-after-the-base]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/developer_job.py
  - runner/session.py
  - runner/milestone.py
  - runner/requests.py
  - runner/bench.py
  - tests/runner/test_loop.py
  - tests/runner/conftest.py
  - tests/runner/test_milestone.py
  - tests/runner/test_backup.py
  - tests/runner/test_cli.py
tests:
  - tests/runner/test_developer_job.py
---

### Goal
A developer ticket's job (its attempts, gates, direction, merge, red main and block) lives in `runner/developer_job.py`, with its tests in `tests/runner/test_developer_job.py`; nothing the runner does changes.

### Context
Read the Decisions in `.softfield/cards/f290-runner-loop-py-is-6-500.md` (D1–D8, and the Replan f290-03 logged), and follow f290-01's and f290-02's commits (`git log -3 --stat`).
- The candidates in `runner/loop.py`: from `def _check_context` to the end of `def _look_at_block` and `def _queue_look` (`def run_task`, `def _develop`, `def _regate`, `def give_direction` and the direction helpers, `def _merge`, `def _check_all`, `def _main_is_red`, `def waits_for_main`, `def block`), applying D3.
- `run_task` hands a lead ticket to `run_lead_task`, which stays in `runner/loop.py` until f290-05: import it inside the function (D4).
- D5: `run_task` is patched on `loop` by the scheduler's tests (they keep patching it there: the scheduler calls it); `run_gates`, `warmup`, `loaded_context_length` and `session_reasoning` are patched on `loop` by tests that run a ticket, and move to `developer_job` with their caller.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D7 for each moved name: many ready tickets name `run_task`, `_merge` or `block` beside `runner/loop.py`.

### Done when
- `runner/developer_job.py` holds a developer ticket's job, at most 1,800 lines, and imports `runner/session.py` and `runner/waits.py` but not `runner/loop.py` at module level
- the moved tests pass in `tests/runner/test_developer_job.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included
