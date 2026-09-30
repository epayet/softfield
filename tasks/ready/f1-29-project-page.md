---
id: f1-29-project-page
milestone: f1
depends_on: [f1-12-milestones-list]
difficulty: 3
files:
  - factory_dashboard/projects.py
  - factory_dashboard/templates/project.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
`/projects/{name}` says what a project is, where it lives, and how its milestones went.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`.
- The page: the project's name and description, its repo path, its milestones newest first with their status (links to `/milestones/{key}`), and its last runs (links to `/runs/{run_dir}`).
- The project name in the top bar links here.
- An unknown project answers 404.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- the fixture's project shows its description, path, milestones with status and runs
- a project with no milestones yet says so
- an unknown project is a 404
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
