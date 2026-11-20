---
id: f132-09-fix-jobs-runs-timeline-plates
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 2
depends_on: [f132-07-timeline-every-project]
finding: f132-cp5
files:
  - factory_dashboard/jobs.py
  - factory_dashboard/templates/jobs.html
  - factory_dashboard/templates/runs.html
  - factory_dashboard/templates/timeline.html
tests:
  - tests/factory_dashboard/test_jobs.py
  - tests/factory_dashboard/test_runs.py
  - tests/factory_dashboard/test_timeline.py
---

### Goal
A job's page takes its own project, and Jobs, Runs and the Timeline show a Project column only when the factory has more than one project; their tests check what the page says.

### Context
Read `.softfield/cards/f132-the-overview-shows-the-whole-factory.md` (D3) and f132-06 / f132-07 in `.softfield/tasks/done/`.
- `job_page` in `factory_dashboard/jobs.py` calls `render(request, conn, detail.ticket or project, ...)`: the ticket's name is passed where the project's goes, so a job page's top bar and `?project=` links carry a ticket id as the project. `run_page` passes the run's project; the job page should do the same (`get_job_detail` already joins `projects p`; it does not select the name).
- f132-06's Done when says "one project only: no plate and no Project column". `jobs.html`, `runs.html` and `timeline.html` always print the `<th>Project</th>` header and a `<td>`; only the plate inside is guarded by `many_projects`. `factory_dashboard/timeline.py` computes `many_projects` but its template never reads it, and prints `bar.project` as bare text instead of the plate.
- The new tests assert `"proj" in html`, `"coucou" in html`, `"other" in html`: `proj` is the class of the always-printed `<td>`, so they pass with no plate drawn. Make them read each row's own Project cell (the row of a given job or run) and assert its plate text; add the one-project case (no `Project` header, no plate) for the three pages.
- The timeline's `?project={{ bar.project }}` link is not url-encoded; the Jobs list's links write `?project=` twice (`{{ q }}&project=`).
- The timeline's milestone filter matches `m.key` across projects, so two projects that both have an `m1` mix their jobs; the new test dodges this with a unique key (`tc-m1`). Add a test with the same key in two projects and say in the test what the page shows.

### Done when
- `/jobs/<id>` of a job with a ticket shows its own project in the top bar and in its links, never the ticket's name
- one project only: `/jobs`, `/runs` and `/timeline` have no Project column and no plate
- two projects: each row's Project cell holds that row's project plate, checked on the row and not on the page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
