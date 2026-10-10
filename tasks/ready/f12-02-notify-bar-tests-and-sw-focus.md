---
id: f12-02-notify-bar-tests-and-sw-focus
milestone: f12-turn-on-notifications-little-feedback-button
depends_on: []
priority: 100
difficulty: 3
files:
  - factory_dashboard/static/sw.js
  - factory_dashboard/static/notify.js
tests:
  - tests/factory_dashboard/test_app.py
finding: f12-01-notifications-asked-once
---

### Goal
The notification bar's tests prove what its ticket asked, and a tap on a notification focuses an open dashboard tab.

### Context
Read `factory_dashboard/static/notify.js` (`setupBar`), `factory_dashboard/static/sw.js` and the `test_notification_bar_*` tests in `tests/factory_dashboard/test_app.py`.
- `test_notification_bar_never_shows_when_permission_granted` and `..._denied` only wait for the bar to be hidden, which it already is in the HTML, so they pass even if `setupBar` showed it. They must first wait for the page to have run `setupBar` (for example wait for `#live-facts` attached, or for the service worker registration), then assert the bar is still hidden.
- The ticket's "Done when" asked for a test of a non-secure address: the bar shows the three numbered steps with this page's own `location.origin`, two Copy links, and **Got it** sets `notify:asked` and hides the bar. No test covers it. `setupBar` picks that branch on `window.isSecureContext`; a test can force it with an init script that defines `isSecureContext` as false.
- `sw.js` is served from the URL path static/sw.js, so its scope is `/static/` and `self.clients.matchAll()` (controlled clients only) never finds a dashboard page at `/`: a tap always opens a new window. Register it with a scope that covers the pages, or match with `includeUncontrolled: true`.
- The yes-test checks `requestPermission` was asked once; also assert `localStorage` `notify:asked` is "1" after Yes.

### Done when
- the granted and denied tests fail if the bar were shown (the page has run its script before the assertion)
- a test on a non-secure address checks the bar's text names the page's origin, and that Got it hides it and stores `notify:asked`
- a tap on a notification focuses an open dashboard tab (`sw.js` finds the page's client)
- the listed tests pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
