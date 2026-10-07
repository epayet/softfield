---
id: f6-16-top-bar-status
milestone: f6-planning-room
depends_on: [f6-14-talk-while-paused]
agent: lead
difficulty: 4
files:
  - factory_dashboard/app.py
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/static/notify.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
Every dashboard page's top bar says, at a glance and live, whether the factory is running, idle, pausing, paused or waiting, with a big Pause or Resume button beside it. The Planning tab's count shows on every page, and the notifications button says what it does.

### Context
Read `factory_dashboard/templates/base.html` (the top bar, the Planning tab, `#notify-me`, `#notify-live`), `render` in `factory_dashboard/app.py`, the live context in `factory_dashboard/overview.py` (`paused_clock`, `pausing`, `running`, `planning_count`, `all_done`), the pause block in `factory_dashboard/templates/_partials/running.html`, the `/live` route and `factory_dashboard/templates/_partials/live.html` (its out-of-band `#planning-tab`), and `offer` in `factory_dashboard/static/notify.js`.
- The owner (2026-10-07): "it would be good to see in a very obvious way from the top bar whether the factory is running, idle (nothing to do) or paused… if there is space in the top bar, a big resume/pause button could be nice there"; "i clicked it, and the button just disappeared. oh wait no, now i see 'pausing after this job' but it took a while"; "planning in menu says - 1 if there is one thing for me to look at… it disappears when i'm on the planning itself"; "what is the notify me button at the top supposed to do?".
- **The status:** one of "Running: <ticket or job>", "Idle: nothing to do", "Pausing after this job", "Paused by you since HH:MM", "Waiting for Claude until HH:MM" (the run's `activity` and `waiting_until`), or "Stopped" (no live run). Colour from the existing tokens, with its words always shown.
- **The button:** Pause while running or idle, Resume while pausing or paused, posting the same requests as `factory_dashboard/templates/_partials/running.html`. On click it shows the asked state at once ("Pausing after this job" or "Resuming…"), not the bare request partial.
- **Live on every page:** the bar's status, the button and the Planning count refresh every 5 s from `/live` (out of band, like `#planning-tab` today), on every page, whether or not notifications are on. The count and the status come from one helper that `render` also calls, so the first paint of every page has them.
- **Notifications:** the button reads "Turn on notifications" and hides once the browser has granted them; it stays as today where the browser can't notify.

### Done when
- `/planning`, `/tickets` and `/` all show the Planning count on first paint, and the same status words
- a test per status: the words and the button (Pause or Resume) for a running job, an idle run, a pause asked, a pause held, a wait for Claude, no live run
- a browser test: pressing Pause in the bar shows "Pausing after this job" at once and posts a `pause` request
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
