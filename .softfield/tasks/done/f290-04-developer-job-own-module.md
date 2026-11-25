---
id: f290-04-developer-job-own-module
agent: lead
milestone: f290-runner-loop-py-is-6-500
difficulty: 5
max_diff: 9000                      # a move counts its lines twice: removed and added
depends_on: [f290-03-replan-after-the-base]
commands: [cp, sed -i]
files:
  - runner/loop.py
  - runner/developer_job.py
  - runner/session.py
  - runner/milestone.py
  - runner/requests.py
  - runner/bench.py
  - runner/owner.py
  - tests/runner/test_owner.py
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
- The range also holds what is not this job's: `def catch_up_plan` and `def both_added` stay in `runner/loop.py` for f290-08 (the planner's); `def _has_branch`, `def _catch_up` and `def _record_refusal` go to `runner/session.py`, since the lead, review and planner jobs and `runner/bench.py` use them too (session is 1,728 lines: keep it at or under D8's 1,800). `def route_developer` (before the range) moves too, as only `_develop` calls it.
- What the lead and review jobs share with this one stays here, and f290-05 and f290-07 import it from `runner/developer_job.py`: `_logs_dir`, `_check_results`, `_check_all`, `_merged_line`, `waiting_behind`, `BLOCKED_KIND`, `blocked_text` and `block` (with `_look_at_block`, `_run_of`, `_queue_look`). `runner/owner.py`, `runner/requests.py` and `tests/runner/test_owner.py` use the last three; `runner/bench.py` imports `_log_running`, `_prompt` and `_read_blocked` from here.
- `_save_thinking` stays here; `after_ticket` in `runner/loop.py` imports it.
- `run_task` hands a lead ticket to `run_lead_task`, which stays in `runner/loop.py` until f290-05: import it inside the function (D4). Likewise `rate_finished` and `current_ratings` (called by `_merge`, `block` and `route_developer`) stay in `runner/loop.py` until f290-06: import them inside their functions with the same comment; f290-06 points them at the rating store.
- D5: `run_task` is patched on `loop` by the scheduler's tests (they keep patching it there: the scheduler calls it); `run_gates`, `warmup`, `loaded_context_length` and `session_reasoning` are patched on `loop` by tests that run a ticket, and move to `developer_job` with their caller.
- For a long move, `cp` the file and delete line ranges with `sed -i 'A,Bd' <file>`; check with `git diff --stat`.
- Then D7 for each moved name: many ready tickets name `run_task`, `_merge` or `block` beside `runner/loop.py`.

### Done when
- `runner/developer_job.py` holds a developer ticket's job, at most 1,800 lines, and imports `runner/session.py` and `runner/waits.py` but not `runner/loop.py` at module level
- the moved tests pass in `tests/runner/test_developer_job.py`, none renamed or edited beyond imports and patch targets, and every other test in `tests/runner/` passes
- no ticket in `.softfield/tasks/ready/` or `.softfield/tasks/later/` names a moved `def` or `class` beside `runner/loop.py`
- all gates pass (see `docs/workflow.md`), mypy included

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
