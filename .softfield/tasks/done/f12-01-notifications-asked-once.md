---
id: f12-01-notifications-asked-once
milestone: f12-turn-on-notifications-little-feedback-button
depends_on: []
priority: 100
difficulty: 4
files:
  - factory_dashboard/static/notify.js
  - factory_dashboard/static/sw.js
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The dashboard asks about notifications once, on the first visit, with its own small bar instead of the top bar's button, and shows them through a service worker so they work on Android too.

### Context
Read `docs/adr/26-notifications-on-the-home-wifi.md` items 2 and 3, `factory_dashboard/static/notify.js`, `factory_dashboard/templates/base.html` (the `#notify-me` button) and `factory_dashboard/static/dashboard.css` (`#notify-me`). Follow the worked example for a dashboard script in `docs/agents/developer.md`: the browser test in `tests/factory_dashboard/test_app.py` that replaces `Notification` with a recording stand-in.
- The bar sits under the top bar, on every page: "Get a notification when something needs you, or when all the work is done?" with **Yes** and **No thanks**. It shows only when the browser supports notifications, the permission is still "default", and this browser hasn't answered the bar before (`localStorage` key `notify:asked`).
- Yes calls `Notification.requestPermission()` (from the tap); either button sets `notify:asked` and hides the bar for good.
- On an address that isn't a secure context, the bar instead gives the steps, numbered: "This address can't show notifications yet. In Chrome: 1. open `chrome://flags/#unsafely-treat-insecure-origin-as-secure` [Copy] in a new tab; 2. paste this address in its box: `<location.origin>` [Copy]; 3. set it to Enabled and tap Relaunch. Then come back here." A page can't link to `chrome://`, hence the Copy buttons (`navigator.clipboard.writeText`, which works on plain http only for a tap; on failure, select the text instead). **Got it** sets `notify:asked` too.
- Remove the `#notify-me` button and its CSS.
- `factory_dashboard/static/sw.js` only shows notifications: no `fetch` handler, no cache. On `notificationclick` it focuses an open dashboard tab, or opens `/`. `notify.js` registers it when `navigator.serviceWorker` exists and shows through `registration.showNotification`; without it, `new Notification` as today.
- What notifies, and when, stays as it is (`compare` in `notify.js`).

### Done when
- every page carries the bar's markup, hidden, and no `#notify-me` button (asserted from the HTML)
- `/static/sw.js` is served
- in the browser test: with permission "default" and nothing stored, the bar shows; No thanks hides it and it stays hidden after a reload; Yes calls `requestPermission` once; with permission "granted" or "denied" the bar never shows; on a non-secure address the bar shows the steps with this page's own address
- checked by hand at review: the bar on desktop and phone, and a notification on the phone once the address is trusted
- the listed tests pass, and fail without the change

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3533
gate_failures: []
tokens: 1951145
```
