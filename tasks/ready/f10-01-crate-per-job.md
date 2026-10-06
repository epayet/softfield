---
id: f10-01-crate-per-job
milestone: f10-crates
depends_on: []
agent: lead
difficulty: 7
files:
  - factory_dashboard/line.py
  - factory_dashboard/static/factory.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
Whatever the runner is doing is one crate on the floor, moving along the belt to the machine doing it. That includes the gates and the lead's finish, so the floor never stands still while something runs.

### Context
Read `docs/milestones/f10-crates.md`, `live_line`, `trips`, `_crates` and `_work` in `factory_dashboard/line.py`, the runner's activity (`runs.activity` and `heartbeat`, written by the loop: "Running: check-all · f6-06-desk-page") and `open_jobs` in `runner/metrics.py`, then `belt`, `machine` and `drawFloor` in `factory_dashboard/static/factory.js`. Then `tests/factory_dashboard/test_line.py`.
- The owner (2026-10-06): one crate moving on the conveyor belt at a time while work is done; a developer working with the belt still; "Running: check-all" with nothing moving.
- Every kind of queued job (F8: checkpoint, review, direction, escalation, planner) and every ticket attempt is a crate. The gates are a crate at Checks.
- Live and replay draw the same motion from the same data.
- Then write `f10-02-replan`'s facts into the milestone doc for the developers' tickets.

### Done when
- with a developer attempt running and no trip logged yet, the queue→developers belt is moving and the crate is on the developer's machine
- with the runner's activity "Running: check-all · <ticket>", the crate is at Checks and the light is on
- a running checkpoint, escalation or planner job each shows its crate on its machine
- a replay at a moment with a running job draws the same crate and belt as live did
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
