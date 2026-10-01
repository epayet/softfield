---
id: f1-35-timeline-milestones-fixes
milestone: f1
depends_on: [f1-12-milestones-list]
difficulty: 4
finding: f1-cp3
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/timeline.py
  - factory_dashboard/templates/timeline.html
  - factory_dashboard/static/charts.js
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_timeline.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_timeline.py
---

### Goal
`/milestones` really lists newest first with its status, and `/timeline` does what f1-11 asked, with tests that would catch a wrong page.

### Context
Read `factory_dashboard/milestones.py`, `factory_dashboard/timeline.py`, `factory_dashboard/static/charts.js` and their two test files. `write_fixture`, `tests/factory_dashboard/test_queries.py`, `tests/factory_dashboard/test_overview.py` and `tests/runner/test_report.py` stay untouched; put new rows in your own `tests/factory_dashboard/conftest.py` function.
- Facts about `/milestones`: a milestone that has merged tickets is built from `queries.trends`, with `status`, `started` and `ended` left as `None`, so its Status cell always shows a dash and its sort key ignores its real date. Those rows sort after the ones from the `milestones` table, and among themselves by key, so `f10` would list before `f2`. `test_milestones_shows_newest_first` passes only because `"f1" < "m4"` as strings. `test_milestone_numbers_match_queries` checks `"3" in row` and `"1" in row`, which any row satisfies. The page docstring promises dates; none are shown. `queries.trends` runs four more times for the charts.
- Facts about `/timeline`: `factory_dashboard/static/charts.js` has no click handler, so a bar never opens `/jobs/{n}` (f1-11 required it; the table's ticket links are the only way). The outcome colours have no `refused`, which f1-11 listed. Refusal markers are read for every project and run, ignoring the milestone and run filters. The select shows "All milestones" when the page is filtering by the default (latest) milestone, because the template gets the raw query value. No test opens the default: `test_running_job_bar_ends_at_render_time` loops and asserts nothing if no bar is running; `test_timeline_has_filter_form_and_jobs_table` only looks for the words "Filters" and "Jobs"; the `run` filter is untested.
- Your previous run's `all-tests` failure (`tests/runner/test_tasks.py::test_queued_tickets_name_only_what_exists_or_an_earlier_ticket_creates`, about f1-36) was on main before you started; it is fixed now and was not caused by your change.

### Done when
- every milestone row shows its status, and rows are ordered by their real start date, newest first, for a fixture where key order and date order disagree
- the milestone row tests check each cell of the F1 and F2 rows (merged, pass rate, escalations, review rounds, dollars, net), not substrings of the whole row
- clicking a timeline bar opens its job page (a behaviour a person would see: the bar's `job_id` goes to `/jobs/{n}`); `refused` has its own colour
- refusal markers follow the page's filters; the select shows the filter actually applied
- tests: the default page shows only the latest milestone's jobs; `?run=` shows only that run's; the running-job test fails if there is no running bar; the jobs table is read row by row (ticket, agent, outcome)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: invalid
attempts: 2
tokens: 6263211
logs: var/runs/20260930-194445/f1-35-timeline-milestones-fixes
```
