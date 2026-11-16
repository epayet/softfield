---
id: f252-01-open-in-a-new-tab
milestone: f252-make-the-open-app-with-docker
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/_partials/app_row.html
tests:
  - tests/factory_dashboard/test_projects.py
---

### Goal
The app row's "Open ↗ :<port>" button on the Projects page opens the app in a new tab, so the dashboard stays where it was.

### Context
- The button is the `<a class="btn go" …>Open ↗ :{{ row.app.url_port }}</a>` in `factory_dashboard/templates/_partials/app_row.html`. F239 chose the same tab (`.softfield/tasks/done/f239-05-app-row-on-projects.md`); the owner reversed that on 2026-11-16 (`.softfield/cards/f252-make-the-open-app-with-docker.md`).
- Follow the links that already open a new tab: `target="_blank" rel="noopener"`, as in `factory_dashboard/templates/milestone.html` (the "Before and after" plate's live link).
- `test_a_running_app_shows_running_stop_open_and_logs` in `tests/factory_dashboard/test_projects.py` asserts the opposite today (`'target="_blank"' not in row`) and checks the link's exact opening tag; update it rather than add a second test.
- Logs, Run, Stop and the plant button stay in the page as they are.

### Done when
- the Open link carries `target="_blank"` and `rel="noopener"`, and its href and text are unchanged
- the Logs link still opens in the same tab
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
