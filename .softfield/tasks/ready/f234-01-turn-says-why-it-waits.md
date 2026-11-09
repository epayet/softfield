---
id: f234-01-turn-says-why-it-waits
milestone: f234-if-it-says-running-picking-the
agent: lead
difficulty: 3
depends_on: []
commands: [rm .softfield/tasks/ready/f234-02-stuck-picking-in-amber.md]
files:
  - .softfield/tasks/ready/f234-02-stuck-picking-in-amber.md
  - runner/loop.py
  - runner/metrics.py
  - tests/runner/test_loop.py
  - tests/runner/test_metrics.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_metrics.py
---

### Goal
A project's run never keeps saying "picking the next ticket" after a turn that ran nothing: it says why it waits. And every run records since when its activity has been what it is.

### Context
Read `.softfield/cards/f234-if-it-says-running-picking-the.md` ("Why it says so today", D1, D2).
- `work_queue` in `runner/loop.py` writes `PICKING` at the top of each turn; under `wait=False` (`run_projects`, `project_round`) the `job is None` branch writes `_idle_line` only when `take_tickets` is true. Make every no-run return under `wait=False` write an idle line (D1). When tickets were held back only because `take_tickets` was false, `_idle_line` says they wait their turn (use `_tickets_wait`), not "nothing can run yet".
- `set_activity` and `doing` in `runner/loop.py` write through `metrics.update_run_activity`; add `runs.activity_since` with a new migration in `runner/metrics.py` (follow the `_V…` blocks and how `activity` and `waiting_until` were added), set to the current UTC ISO time when the activity's text differs from the stored one, kept when it is the same, and cleared when the activity is cleared.
- The dashboard reads `activity_since` in f234-02-stuck-picking-in-red: don't touch `factory_dashboard/`.
- Housekeeping: `.softfield/tasks/ready/f234-02-stuck-picking-in-amber.md` is an earlier draft of f234-02-stuck-picking-in-red, left on the plan branch because a planner job can't delete a file. Delete it in this ticket's commit (`rm`, listed in `commands:`).

### Done when
- two projects in `run_projects`, the first running a job each round and the second with only lead tickets it can't take: after the round, the second's `runs.activity` starts with "Idle: ", never "picking the next ticket"
- a project whose ticket turn was skipped because an earlier project ran one says its tickets wait for their turn
- `.softfield/tasks/ready/f234-02-stuck-picking-in-amber.md` is gone; f234-02-stuck-picking-in-red stays
- `update_run_activity` with the same text twice keeps `activity_since`; a new text resets it; None clears both
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
