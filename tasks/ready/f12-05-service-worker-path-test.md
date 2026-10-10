---
id: f12-05-service-worker-path-test
milestone: f12-turn-on-notifications-little-feedback-button
depends_on: [f12-03-remove-review-probe]
priority: 100
difficulty: 3
finding: f12-turn-on-notifications-little-feedback-button-F7
tests_only: true
files:
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
A test proves that, with a service worker registered, the dashboard shows its notifications through it: the path a phone uses, which no test runs today.

### Context
Read `show` and `registerSw` in `factory_dashboard/static/notify.js`, and `test_the_page_notifies_once_per_new_item_and_once_when_all_is_done` with `FAKE_NOTIFICATION` in `tests/factory_dashboard/test_app.py`. The code is right; only tests change (`tests_only`).
- In the existing tests the service worker never registers, so every notification goes through `new Notification`, which `FAKE_NOTIFICATION` records in `window.shown`. On Android, Chrome shows only what goes through `registration.showNotification`.
- Add a second init script that puts a stand-in at `navigator.serviceWorker` (`Object.defineProperty(navigator, "serviceWorker", { value: … })`). Its `register(url)` records the url and resolves to an object whose `showNotification(title, options)` records the title, `options.body` and `options.tag` in a list of its own (not `window.shown`).
- Follow the existing test for the rest: `FAKE_NOTIFICATION` with its permission already "granted" (see `FAKE_NOTIFICATION_GRANTED`), `open_overview(page, serve_between(…))`, wait for the first compare (`localStorage.getItem('notify:coucou') !== null`), then add a Needs-you item with `metrics.upsert_owner_item` and wait for the notification.
- A second test: the same, with a stand-in whose `showNotification` rejects (`async () => { throw new Error("no") }`). `show` then falls back to `new Notification`.

### Done when
- first test: `register` was called once with `/static/sw.js`
- first test: the new item gave exactly one entry in the stand-in's list, with the title "Needs you", the item's text as its body and a tag that isn't empty, and `window.shown` stayed empty
- second test: with a `showNotification` that rejects, the item appears exactly once in `window.shown`
- only `tests/factory_dashboard/test_app.py` changes
- all gates pass (see `docs/workflow.md`)
