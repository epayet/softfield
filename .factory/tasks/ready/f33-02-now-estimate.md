---
id: f33-02-now-estimate
milestone: f33-overview-now-check-all-how-long
depends_on: [f33-01-activity-clock]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
Now says how long the work it shows has been running and roughly how long it has left, for a job and for the runner's own work between jobs (check-all, the gates).

### Context
Read `.factory/cards/f33-overview-now-check-all-how-long.md` (D2), `factory_dashboard/templates/_partials/running.html` (Now), `running_jobs`, `LiveRun` and `typical_activity` in `factory_dashboard/overview.py`, then `_typical` and `_next_reply` in `factory_dashboard/planning.py`, the worked example for the estimate's words.
- Move `_typical` into `factory_dashboard/overview.py` as `typical_job`, beside `running_jobs`; `factory_dashboard/planning.py` imports it, so both pages give the same estimate.
- Each card in Now, a job's or a run's, shows "Running for <time>" and, when an estimate exists, one of: "About <time> left"; "Any minute now" within a minute; "Longer than usual (about <typical>)" once past it. A run's estimate is `typical_activity` of its activity's kind (the words before " · ").
- A run that holds ("paused by you") or waits for Claude's limit shows neither line.

### Done when
- with check-all running for 2 min and past check-alls of 5 min, Now shows "Running for 2 min" and "About 3 min left"
- a job's card shows the same two lines from its role's and agent's past jobs; with no history, only "Running for"
- past the typical time, "Longer than usual (about 5 min)"; within a minute of it, "Any minute now"
- the planning room's "next reply" estimate is unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
