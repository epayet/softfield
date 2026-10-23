---
id: bug-22-a-run-records-its-ticket
milestone: bugs
difficulty: 5
depends_on: []
agent: lead
area: factory
priority: 48
finding: f3-review
files:
  - runner/loop.py
  - runner/metrics.py
  - factory_dashboard/overview.py
tests:
  - tests/runner/test_metrics.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
A waiting run's ticket title on the Overview comes from the ticket id the runner records, not from splitting its activity text.

### Context
Read `def live_runs` in `factory_dashboard/overview.py` (it splits `runs.activity` on " · " and takes the next word as the ticket), the `runs` table and its migrations in `runner/metrics.py`, and where `runner/loop.py` writes the activity. `runner/**` is protected: tests first.
- Record the ticket id on the run beside its activity (a new nullable column, cleared when the activity names no ticket), and have `live_runs` read it.

### Done when
- a run "waiting for Claude · f2-06-overview-allowances until 01:40" shows that ticket's title
- an activity whose wording changes ("waiting · for f2-06 …") still shows it, since the id comes from the column
- a run with no ticket shows no title
- an older database gets the column on open
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
