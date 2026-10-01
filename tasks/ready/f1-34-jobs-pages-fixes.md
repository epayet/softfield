---
id: f1-34-jobs-pages-fixes
milestone: f1
depends_on: [f1-09-job-page]
difficulty: 3
finding: f1-cp1
files:
  - factory_dashboard/templates/jobs.html
  - factory_dashboard/jobs.py
  - tests/factory_dashboard/test_jobs.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_jobs.py
---

### Goal
`/jobs` shows what f1-08 asked: readable cells, a link to each job, and tests that would catch a wrong list.

### Context
Read `factory_dashboard/templates/jobs.html`, `factory_dashboard/jobs.py` and `tests/factory_dashboard/test_jobs.py`; the tokens filter is in `factory_dashboard/app.py` and `factory_dashboard/templates/overview.html` shows how it is used.
- Facts about the page today: rows never link to `/jobs/{n}` (f1-08 required it). The template is autoescaped, so `"&ndash;"` inside `{{ }}` prints as `&amp;ndash;` (the literal text `&ndash;` on screen); a test that accepts `&amp;ndash;` accepts the bug. The tokens cells compute `job.tokens_in / 1000 | int` (the filter binds to `1000`, so a float such as `200.0` is printed) and always append `k`, so a job without tokens reads `&ndash;k`. `minutes` of 0 shows as missing.
- **Facts about the fixture: `/jobs` under `client_with_jobs` lists 12 jobs, not 16.** `db_path` calls `write_fixture` (11 jobs), then `client_with_jobs` calls `write_jobs`. But `runner.metrics.start_job` upserts on (run, ticket, role, attempt) (the `jobs_key` index in `runner/metrics.py`): writing the same key again updates the existing row, keeps its id and keeps the fields `finish_job` isn't given. Four of `write_jobs`' five jobs (f1-01-first developer 1, f1-02-escalated direction 1 and escalation 1, m4-01-old developer 1) have the same key as a `write_fixture` job, so they update it; only `f1-04-live` is a new row. The existing overflow test agrees: "200 of 217" is 12 + 205.
- After `write_jobs`, by id: 1 f1-01-first developer (10:00, gates all ok), 2 and 3 f1-02-escalated developer attempts 1 and 2, 4 f1-02-escalated direction (now started 10:05, failed at gate `tests`), 5 last-attempt, 6 escalation (now started 10:15), 7 lead-ticket, 8 review and 9 checkpoint (no ticket), 10 m4-01-old (2026-09-20T09:00), 11 m4 review (no ticket, same second), 12 f1-04-live (running, started `2026-10-02T11:48:00+00:00`, no tokens, no end). Times are 2026-09-30, +02:00, unless said. Same-second ties are ordered by id, newest id first.
- So `?agent=claude-opus&role=escalation` matches exactly one job (id 6), and the `LIMIT 1` queries in `client_with_jobs` find the right rows. Only job 4 has a failed gate. m4-01-old has `tokens_out` 0.
- Facts about the tests: `test_filter_by_agent_and_role_shows_only_matching`'s last assertion is always true. `test_no_filter_shows_all_jobs_newest_first` only compares two dates, and `test_failed_attempt_shows_failed_gate_name` looks for `tests` anywhere in the section.
- The job page (`/jobs/{job_id}`) does not check the job belongs to the project shown.

### Done when
- every row links to its `/jobs/{n}`; a job without tokens or minutes shows a dash (`–` on screen, not `&ndash;`), and tokens read like `200k` (as the overview shows them)
- a test reads the table rows and checks, row by row, the order of all 12 jobs (same-second ties by id), and that the row of the failed job shows `tests` in the failed-gate cell while the others show a dash there
- the agent and role filter test asserts the exact set of job rows returned (and that the other rows are absent)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 5128777
logs: var/runs/20260930-194445/f1-34-jobs-pages-fixes
```

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: no-changes)
attempts: 3
tokens: 1903550
logs: var/runs/20260930-194445/f1-34-jobs-pages-fixes-run2
```
