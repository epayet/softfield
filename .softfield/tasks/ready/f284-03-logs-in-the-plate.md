---
id: f284-03-logs-in-the-plate
milestone: f284-i-find-the-docker-run-buttons
difficulty: 3
depends_on: [f284-02-the-busy-row]
files:
  - factory_dashboard/stacks_routes.py
  - factory_dashboard/templates/_partials/app_row.html
  - factory_dashboard/templates/app_logs.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_stacks_routes.py
---

### Goal
Logs opens under the app's row on the Projects page, live while open, and shows the image build while the app starts; the logs page shows the build too, and says so when the app has no lines yet.

### Context
The picture to build is the Proposed side of `.softfield/cards/f284-mockup/app-row.html` (the open logs under duck-ascii-test, and the logs page at the bottom). Read D7 and D8, and "As built" if there is one, in `.softfield/cards/f284-i-find-the-docker-run-buttons.md`; then `logs`, `build_lines` and `StackState.busy` in `runner/stacks.py`, `logs_page` in `factory_dashboard/stacks_routes.py`, `factory_dashboard/templates/app_logs.html`, and the row in `factory_dashboard/templates/_partials/app_row.html` (f284-02).
- `GET /projects/{name}/logs/tail` answers a partial: the last 40 lines of `logs(stack, lines=40)`, and, when the app is busy or its state is "update failed", `build_lines(stack)` above them under a "Build" label. A GET: no guard; 404 as the logs page.
- In the row, Logs becomes a button with `aria-expanded`: pressed, it opens a box under the row that loads the tail and asks for it every 5 s (`[window.liveIdle()]`) while open; pressed again, it closes and stops asking. The box is 12 lines tall, scrolls, stays at the bottom unless the owner scrolled up (as `app_logs.html` does). Its bar has "All lines →" to `/projects/<name>/logs`, same tab.
- The box must survive the row's own 5 s refresh from f284-02: put it outside the swapped `.app-row` element, or keep it open across the swap; a test checks one refresh doesn't close it.
- Logs page: the same Build part while busy, and "No lines yet: the app hasn't started." instead of an empty block. Its Pause stays as it is.
- Lines are escaped text in the mono font. CSS in the app row's block of `dashboard.css`, on the tokens.

### Done when
- `/projects/<name>/logs/tail` shows the last app lines, and the build's lines under "Build" when the app is busy
- the row's Logs button opens the box with `aria-expanded="true"` and the 5 s trigger, and a second press closes it
- the logs page of a busy app shows the build's lines; of an app with no lines, "No lines yet: the app hasn't started."
- an unknown project answers 404 on the tail
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
