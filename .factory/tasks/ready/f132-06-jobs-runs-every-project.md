---
id: f132-06-jobs-runs-every-project
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 3
depends_on: [f132-02-overview-live-every-project]
files:
  - factory_dashboard/jobs.py
  - factory_dashboard/runs.py
  - factory_dashboard/templates/jobs.html
  - factory_dashboard/templates/runs.html
tests:
  - tests/factory_dashboard/test_jobs.py
  - tests/factory_dashboard/test_runs.py
---

### Goal
Jobs and Runs list every project's, newest first, each row with its project's plate, whichever project is picked.

### Context
Read `.factory/cards/f132-the-overview-shows-the-whole-factory.md` (D2–D4).
- `factory_dashboard/jobs.py` (the list's query and its filters, `job_page`) and `list_runs`, `get_run` in `factory_dashboard/runs.py` filter on the picked project's name.
- `every_project` (`factory_dashboard/overview.py`, f132-02) gives the projects; the plate is f132-02's project plate partial in `factory_dashboard/templates/_partials/`, shown when `many_projects` is true. Follow how f132-02 uses both in `factory_dashboard/templates/_partials/queue.html`.
- Each row gets a Project column with its plate; every link in a row (its ticket, its job, its run) carries the row's own `?project=`.
- A job's or a run's own page finds it by id or run folder in any project, not only the picked one.
- The other filters (milestone, ticket, agent, role, outcome) keep working.

### Done when
- with jobs in softfield and travel-companion: `/jobs` shows both, newest first, each with its plate, for either project picked; the total counts both
- a filter by ticket or milestone still narrows the list
- `/jobs/<id>` of a travel-companion job opens while softfield is picked
- `/runs` lists every project's runs, each with its plate; `/runs/<run_dir>` opens for any project's run
- one project only: no plate and no Project column
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
