---
id: f284-02-the-busy-row
milestone: f284-i-find-the-docker-run-buttons
difficulty: 3
depends_on: [f284-01-start-in-the-background]
files:
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/templates/_partials/app_row.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_stacks_routes.py
  - tests/factory_dashboard/test_projects.py
---

### Goal
A project's app row shows a start, a stop or an update while it happens, with how long it has taken and its last build line, and keeps itself up to date until it settles, without a reload.

### Context
The picture to build is the Proposed side of `.softfield/cards/f284-mockup/app-row.html` (the duck-ascii-test and travel-companion rows). Read D3, D5 and D6, and "As built" if there is one, in `.softfield/cards/f284-i-find-the-docker-run-buttons.md`; then `StackState.busy`, `build_lines` and the new words in `runner/stacks.py` (f284-01), and `AppRow`, `row_of` and `app_row` in `factory_dashboard/stacks_routes.py`.
- `GET /projects/{name}/app` in `stacks_routes.py` answers `factory_dashboard/templates/_partials/app_row.html` for the project, from `row_of`; same 404s as the logs page (`stack_of`). It is a GET: no guard, no write.
- A busy row (`row.app.busy`) asks for that address every 5 s with htmx (`hx-trigger="every 5s [window.liveIdle()]"`, `hx-swap="outerHTML"` on itself, as the other live parts in `factory_dashboard/templates/`); a settled row carries no trigger, so polling stops once the answer is settled.
- A busy row: the class `busy`, the word ("Starting", "Stopping", "Updating"), the hazard lamp pulsing, the dashed hazard edge `.app-row.htmx-request` already uses, then in `app-detail` what is happening and since when ("Building the image · 1 min 40 s", "Stopping · 4 s", "Updating to main a1b2c3d · 2 min"), and the last build line from `detail`. No Run and no Stop while busy; Logs stays.
- Elapsed time is computed on the server from `since` at each answer (no clock script); under a minute in seconds, then "N min S s".
- The pulse is a status, so it may move: a slow opacity animation on `.app-row.busy .app-lamp`, off under `prefers-reduced-motion`. CSS goes in the app row's block of `dashboard.css`, on the tokens.

### Done when
- a busy app's row on `/projects` says "Starting", shows "Building the image" and its elapsed time, has no Run or Stop button, and carries the 5 s trigger to `/projects/<name>/app`
- a running app's row carries no trigger
- `GET /projects/<name>/app` answers the row, and 404 for an unknown project
- `test_the_projects_page_lays_out_at_phone_and_display_sizes` still passes at both sizes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
