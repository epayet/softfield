---
id: f124-02-pause-on-the-projects-page
milestone: f124-pause-one-project-from-the-projects
difficulty: 3
depends_on: [f124-01-a-project-pauses-alone]
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/projects.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
Each project on the Projects page has a Pause or Resume button that asks the runner for that project alone, shown on its way at once, and a paused project says so.

### Context
The picture to build: the Proposed side of `.softfield/cards/f124-mockup/projects.html`. Read D5 in `.softfield/cards/f124-pause-one-project-from-the-projects.md`.
- The page is `projects_page` in `factory_dashboard/projects.py`, template `factory_dashboard/templates/projects.html`, styles under "The Projects page" in `factory_dashboard/static/dashboard.css`.
- The requests are `pause_project` and `resume_project`, posted to `/requests` with no subject and the row's project as `project` (the order form in the same template posts the same way); follow the worked example for a button that asks the runner in `.softfield/developer.md`.
- `ProjectCard.paused` already carries the column; `paused_by_you` in `runner/metrics.py` gives the time a project was paused by you, None otherwise.
- On its way: the project's latest `pause_project` or `resume_project` row with no `done`, read as `order_on_its_way` reads the order.
- The paused edge and line use `--warn`, as the top bar's pause does; the on-its-way dashed edge is `--opus`, as `.place input.asked`.

### Done when
- a running project shows Pause; a project paused by you shows a hazard left edge, "Paused by you since HH:MM. Its tickets wait; its planning still answers you." and Resume
- pressing either turns it "Pausing…" or "Resuming…", dashed orange and disabled, with "On its way: the runner takes it at its next pick, after the job it is on", before the answer comes, and after a reload while the request is open
- a project being set up keeps its line and has no button
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
