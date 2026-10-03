---
id: f3-04-clog-today
milestone: f3
depends_on: [f3-07-replay-controls]
agent: lead
difficulty: 5
files:
  - factory_dashboard/line.py
  - factory_dashboard/queries.py
tests:
  - tests/factory_dashboard/test_line.py
  - tests/factory_dashboard/test_queries.py
---

### Goal
The line's document says what clogged the factory today, in four numbers the owner can act on.

### Context
Read `docs/milestones/f3.md` D11 ("What clogged the line today"), `docs/agents/lead.md` (sign-off sheet item 7), section 7 of `docs/reviews/f2.md` (how it was counted by hand), `runner/metrics.py` (the `runs`, `jobs`, `usage_events` and `owner_items` tables) and `factory_dashboard/line.py` (f3-01). Test-first.
- **Decide what each number is computed from, and write it in D11.** Count since local midnight, in minutes:
  1. Waiting for Claude's limit: parked jobs, refusals and their resets, and runs' `waiting_until`.
  2. Failed attempts: the durations of failed developer jobs.
  3. Machines idle while another job ran: per developer machine, the share of the runner's live time without a job of its own while any job ran.
  4. Stopped for the owner: open owner items while no job ran.
- If a number can't be computed faithfully from what's recorded, record what's missing (a new `usage_events` kind, a `runs` column), test-first, rather than guessing.
- `queries.clog(conn, project, since, now)` returns them; `live_line` puts them under `clog`. The milestone report (`runner report`) may reuse it later.

### Done when
- on a fixture day with a 30 min park, two failed attempts (12 and 19 min), and one developer job running while two machines idle, the numbers come out as 30, 31 and the idle shares, with 0 for the owner
- a day with no runs gives zeros, not errors
- `uv run runner check-all --task f3-04-clog-today` passes
