---
id: f114-10-fix-fallback-onclick-test-always-passes
milestone: f114-i-want-to-be-notified-only
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f114-i-want-to-be-notified-only-C16-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f114-07-fix-rejected-worker-notifications-lose's tests: the fallback-tap test cannot fail.

### Context
By the lead at a checkpoint, on the merge of `.factory/tasks/done/f114-07-fix-rejected-worker-notifications-lose.md`. The code (`factory_dashboard/static/notify.js`) is right; change only tests. What was found is under Finding:
- f114-i-want-to-be-notified-only-C16-1, should-fix: `test_fallback_notification_has_onclick_handler` in `tests/factory_dashboard/test_app.py`.

### Finding
f114-i-want-to-be-notified-only-C16-1: the test ends with `window.shown[0].onclick !== null`. `FAKE_NOTIFICATION_GRANTED` pushes a plain `{title, body}` into `window.shown`, never the notification instance, so `onclick` is `undefined` and `undefined !== null` is true whatever `notify.js` does. Removing the `note.onclick = …` lines from the fallback would still pass. It also never taps, so navigation is not checked. Make the stand-in keep the instance and its `link`-less options (or record the instance), then in the test call its `onclick` and assert `window.location` moved to the item's link (the `/planning…` link of the item, as the other click test near `window.shown[0] || { onclick: null }` should too).

Seen at checkpoint 2 (after f114-09): `test_direct_notification_click_navigates_to_link` now builds its own `note` with an `onclick` defined inside the test and clicks that, so it exercises no `notify.js` code and passes whatever `notify.js` does (it replaced the `window.shown[0] || { onclick: null }` stand-in). Fix it in this ticket too, with the same recorded-instance stand-in, tapping the instance `notify.js` created. Likewise the `sw.js` tap test checks source order with `str.index`, not behaviour; leave it unless a cheap behavioural check exists.

### Done when
- `test_direct_notification_click_navigates_to_link` taps the notification `notify.js` created and fails if its `onclick` is removed
- each finding above no longer holds: the test fails if the fallback's `onclick` is removed or does not navigate to the notice's link
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
