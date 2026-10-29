---
id: f177-01-own-cost-per-job
milestone: f177-planner-replies-cost-half-of-claude
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/metrics.py
  - runner/backfill.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_backfill.py
---

### Goal
A Claude job that resumes a session records its own cost, not the session's running total, and the jobs already recorded are corrected.

### Context
Read D1 and "What was found" in `.factory/cards/f177-planner-replies-cost-half-of-claude.md`, then `finish_job` and `MIGRATIONS` in `runner/metrics.py`, and where `runner/backfill.py` reads `total_cost_usd`.
- `claude -p --resume` reports in `total_cost_usd` the whole session's cost so far; `run_claude` (`runner/claude.py`) passes it on as is, and leave it so: the subtraction belongs where the row is written.
- `finish_job`: when it is given both `cost_usd` and `session_id`, it stores `cost_usd` minus the sum of `cost_usd` of the other jobs with that `session_id` (never below 0). A job with no session, or the first of its session, is unchanged.
- The new migration step fixes the rows already there, each session in `started` order: own = its `cost_usd` minus the previous row's `cost_usd` in the same session (the old values are running totals, so subtract the previous one, not a sum). Rows without a session or a cost are left alone. A migration runs once per database, so it can't subtract twice.
- `runner/backfill.py` builds rows from logs: a log of a resumed session gets the same subtraction, against the rows already in the database for that session.
- After the migration, the week of 2026-10-19's planner jobs come to about $71.36 on the live database (the card has the figures); don't open or migrate the live file from the job: the runner's next start does.

### Done when
- a second job on a session with a first job of $1.00 and a result total of $1.26 is stored as $0.26
- the migration turns a session's recorded 0.92, 1.10, 1.18 into 0.92, 0.18, 0.08, and leaves jobs without a session as they were
- a backfilled log of a resumed session stores its own cost
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
