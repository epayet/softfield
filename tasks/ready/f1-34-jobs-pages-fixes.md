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
- Facts about the fixture (read `tests/factory_dashboard/conftest.py` from `db_path` down, not only `write_jobs`): `client_with_jobs` takes `db_path`, and `db_path` already calls `write_fixture`. So `/jobs` lists `write_fixture`'s 11 coucou jobs **plus** `write_jobs`' 5, not 5. It does not include `write_live`: `client_with_jobs` builds its own app instead of using `serve`. Every `write_fixture` job goes through `_job`, which starts it at `2026-09-30T10:00:00+02:00`, the same second as `write_jobs`' `f1-01-first` job. So most rows tie on `started` and their order is decided by id. Three `write_fixture` jobs have no ticket (two reviews, one checkpoint): their ticket cell has no link.
- `write_fixture` already has, for `f1-02-escalated`, a `direction` job and an `escalation` job by `claude-opus`, both passed. So `?agent=claude-opus&role=escalation` matches two jobs, not one. And the `LIMIT 1` queries in `client_with_jobs` may return `write_fixture`'s rows rather than `write_jobs`' (the `direction` query also filters on `outcome = 'failed'`, which only `write_jobs`' has).
- Facts about the tests: `test_filter_by_agent_and_role_shows_only_matching`'s last assertion is always true. `test_no_filter_shows_all_jobs_newest_first` only compares two dates, and `test_failed_attempt_shows_failed_gate_name` looks for `tests` anywhere in the section. The f1-09 tests add `write_jobs` rows (an escalation job) after the fact.
- The job page (`/jobs/{job_id}`) does not check the job belongs to the project shown.

### Done when
- every row links to its `/jobs/{n}`; a job without tokens or minutes shows a dash (`–` on screen, not `&ndash;`), and tokens read like `200k` (as the overview shows them)
- a test reads the table rows and checks, row by row, the order of all the jobs the fixture writes (same-second ties by id), and that the row of the failed job shows `tests` in the failed-gate cell while the passing ones show a dash there
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
