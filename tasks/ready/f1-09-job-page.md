---
id: f1-09-job-page
milestone: f1
depends_on: [f1-08-jobs-list]
difficulty: 4
files:
  - factory_dashboard/jobs.py
  - factory_dashboard/templates/job.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_jobs.py
---

### Goal
`/jobs/{n}` shows one job in full.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). The list is in `factory_dashboard/jobs.py`, its router already registered in `factory_dashboard/app.py`; add the page there. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put the rows your page needs in a function of your own (as `write_live` is), not among f1's or m4's tickets and jobs.
- Facts: backfilled jobs have no `context_limit` (show the peak alone), and a backfilled Claude job may have no `cost_usd`. A job's findings are those with its `findings.job_id`.
- Breadcrumbs: project › milestone › ticket › job.
- Panels: what (role, agent, attempt, outcome, routing reason); time and tokens (start, minutes, tokens in / cached / out or requests, dollars, steps, peak context against the limit as a bar); the gates in order, each with pass or fail, seconds and its log path; the note, if any; the findings this job raised; the session id and log paths.
- The edit streak reads "N edits in a row without running a test or check"; refused commands show as a count.
- An unknown id answers 404.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- a failed attempt shows every gate in order with the failed one marked, and its peak context as "166k of 184k"
- a Claude escalation shows its dollars and its note
- a review job lists its findings with their severity
- `/jobs/999999` is a 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
