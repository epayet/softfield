---
id: f59-01-reports-week-numbers
milestone: f59-periodic-review-of-the-factory
difficulty: 4
depends_on: []
files:
  - factory_dashboard/reports.py
  - tests/factory_dashboard/test_reports.py
tests:
  - tests/factory_dashboard/test_reports.py
---

### Goal
One function gives a week's numbers for a list of projects, with the week before, and the same numbers for every week as a series, from the metrics database.

### Context
Read `.factory/cards/f59-periodic-review-of-the-factory.md` (D1, D2, D3) and follow `factory_dashboard/queries.py`: its `savings` for how a project's rows are read, its dataclasses for the shape, and `is_claude` for which agent costs dollars.
- The new module is `factory_dashboard/reports.py`: `week(conn, projects, monday)`, `weeks(conn, projects)` and `series(conn, projects)`, as D3 lists. No route yet: ticket 02 adds the page to this module.
- A job belongs to its project through `runs.project_id`; tickets merged are `passed` jobs of role developer, last-attempt or lead-ticket; timeouts are jobs whose outcome is `timeout`.
- Weeks run Monday 00:00 to Monday 00:00 in local time; `started` and `ended` are stored with their offset, so compare them as datetimes, not as text.
- Tests build their database as `tests/factory_dashboard/test_queries.py` does.

### Done when
- `week` for two projects counts both; for one, only its own jobs and milestones
- a job started Sunday 23:30 local counts in that week, one started Monday 00:10 in the next
- dollars are by role and only for Claude agents; hours are `ended - started` by agent, a job with no `ended` left out
- developer attempts and passed are by agent; a week with no developer attempt gives no rate (None), not 0
- each number also has its value for the week before
- savings sum `queries.savings` over the milestones whose `ended` falls in the week
- `weeks` lists every Monday from the first job's week to this one, newest first, weeks with no job included; `series` is the same weeks, oldest first
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 3856804
logs: .factory/var/runs/20261027-005355/f59-01-reports-week-numbers
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
