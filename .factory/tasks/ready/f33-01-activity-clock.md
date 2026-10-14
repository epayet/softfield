---
id: f33-01-activity-clock
milestone: f33-overview-now-check-all-how-long
depends_on: []
agent: lead
difficulty: 4
files:
  - runner/loop.py
  - runner/metrics.py
  - factory_dashboard/overview.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_loop.py
---

### Goal
The runner records when its own work between jobs (check-all, the gates, the warm-up) started, and how long each took, so Now can show its time and estimate it.

### Context
Read `.factory/cards/f33-overview-now-check-all-how-long.md` (D1), `set_activity` and `doing` in `runner/loop.py`, `update_run_activity` and the `ALTER TABLE runs ADD COLUMN activity` migration in `runner/metrics.py`, then `LiveRun` and `live_runs` in `factory_dashboard/overview.py`.
- `runs.activity_since`: set with the activity, cleared with it; `doing` restores the earlier activity's `since` along with its words.
- `activity_spans` (run, kind, started, ended): one row when a `doing` block ends. The kind is the activity's words before " · ", with "check-all on main" counted as `check-all`. Waiting for Claude and "paused by you" aren't work: no span.
- `LiveRun` gains `since` (from `activity_since`), and `overview.py` gains `typical_activity(conn, project, kind)`: the average of the last 10 spans of that kind, `None` without any.

### Done when
- while check-all runs, `live_runs` returns its run with `since` set to when check-all began; after it, the earlier activity comes back with its own `since`
- each finished check-all, gates and warm-up leaves one span; a wait or a pause leaves none
- `typical_activity` averages the last 10 spans of a kind, and is `None` with none
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
