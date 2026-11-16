---
id: f250-02-browser-all-done-goes
milestone: f250-i-want-a-notification-when-the
difficulty: 2
depends_on: [f250-01-factory-done-notifies]
files:
  - factory_dashboard/static/notify.js
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The browser no longer shows its own "All work done" notification: the runner's phone notification (f250-01) says it for the whole factory.

### Context
Read D5 in `.softfield/cards/f250-i-want-a-notification-when-the.md`. In `factory_dashboard/static/notify.js`, `compare` pushes the "all-done" notice from `data-all-done` and keeps `done` per project in `notify:seen`; `#live-facts` carries `data-all-done` (`factory_dashboard/templates/_partials/live.html`), from `all_done` in `_live_context` (`factory_dashboard/overview.py`).
- Remove the "All work done" notice from `compare`, and the `done` map from what it stores; an old stored value with `done` in it is still read without error.
- Remove `data-all-done` and `all_done` if nothing else reads them (search the code and templates first); keep them otherwise and say why in your report.
- The other notifications (`data-notices`, one per look, the bundle) don't change. The permission bar's words ("…or when all the work is done?") stay: the phone still says it.
- In the tests, remove or rewrite those that expect "All work done" from the browser; keep the ones about the other notifications as they are.

### Done when
- a project's queue emptying with a dashboard page open shows no browser notification
- a new open item still notifies as before, alone or bundled
- a stored `notify:seen` from before the change (with its `done` map) doesn't break the next look
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
