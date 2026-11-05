---
id: f228-01-trends-reads-once
milestone: f228-loading-the-overview-page-is-slow
difficulty: 3
depends_on: []
files:
  - factory_dashboard/queries.py
  - factory_dashboard/milestones.py
tests:
  - tests/factory_dashboard/test_queries.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
Each milestone's trend no longer works out the lead's rates again, so `trends` costs far less on a project with many milestones and the Milestones page calls it once.

### Context
Read `.softfield/cards/f228-loading-the-overview-page-is-slow.md` ("What happens today", D1, D2).
- `factory_dashboard/queries.py`: `trends` calls `savings` per milestone; `savings` runs `_lead_rates` each time, and `_lead_rates` runs one query per lead ticket.
- Make `_lead_rates` one query, a join of the lead tickets and their jobs. A lead ticket with no lead job still adds nothing, its lines included.
- Make `trends` call `_lead_rates` once and pass the rates to `_milestone_savings`. It must return what `savings(conn, project, key)` returns for that key, so reuse the same combining step. `savings` keeps its signature: `factory_dashboard/reports.py` calls it.
- `factory_dashboard/milestones.py`: `milestones_list` reaches `trends` five times, through `milestone_rows` and the four charts (`_rate_chart`, `_esc_chart`, `_dollars_chart`, `_savings_chart`). Call it once in `milestones_list` and hand the result to all five. `milestone_rows` keeps working when called with only `conn` and `project`: tests call it that way.
- `milestone_rows` also runs its "SELECT t.milestone_id" query inside its loop, once per milestone. Run it once, before the loop.

### Done when
- `trends` runs the same number of SQL statements with 1 lead ticket as with 10 (count them with `conn.set_trace_callback`)
- `_lead_rates` runs one SQL statement, however many lead tickets there are
- one `GET /milestones` calls `trends` once (count the calls with `monkeypatch`)
- `trends`, `savings` and the Milestones page give the same numbers as before: the existing tests in the listed files pass unchanged
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
