---
id: f12-04-copy-says-copied
milestone: f12-turn-on-notifications-little-feedback-button
depends_on: [f12-03-remove-review-probe]
priority: 100
difficulty: 3
finding: f12-turn-on-notifications-little-feedback-button-F6
files:
  - factory_dashboard/static/notify.js
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On the notification bar's steps, each Copy is a real button and says "Copied" once it has copied, so the owner sees the tap worked.

### Context
Read `setupBar` in `factory_dashboard/static/notify.js` (the branch for an address that isn't secure), the `#notify-bar` rules in `factory_dashboard/static/dashboard.css`, and `test_notification_bar_shows_steps_on_insecure_origin` with its helper `_open_at` in `tests/factory_dashboard/test_app.py`: that test opens the page at a plain-http address (`LAN`), where the steps show. Write your test the same way.
- Today each Copy is an `<a class="copy-link">` with no `href`: the keyboard can't reach it, and after a tap nothing on the page changes.
- Make each one a `<button type="button" class="copy-link">`. Keep the class: the existing test counts `.copy-link`. It must still look like a small link in the sentence, not like the bar's Yes button: the rules for `#notify-bar [role=actions] button` must not apply to it, and the `a.copy-link` rules need the new element.
- After the text is copied, by `navigator.clipboard.writeText` or by the fallback below it, the button's own label reads "Copied". The other button still reads "Copy".
- At a plain-http address `navigator.clipboard` doesn't exist, so a test can put a recording stand-in there with an init script, as `FAKE_NOTIFICATION` does for `Notification` in the same test file.

### Done when
- a browser test at the `LAN` address: both Copy controls are `button` elements with the label "Copy"
- after a tap on the first, its label is "Copied", the second still reads "Copy", and the stand-in clipboard received exactly `chrome://flags/#unsafely-treat-insecure-origin-as-secure`
- after a tap on the second, the stand-in received the page's own address (`LAN`), and its label is "Copied"
- the listed tests pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3363
gate_failures: []
tokens: 885779
```
