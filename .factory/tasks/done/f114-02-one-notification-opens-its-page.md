---
id: f114-02-one-notification-opens-its-page
milestone: f114-i-want-to-be-notified-only
difficulty: 5
depends_on: [f114-01-notices-say-what-and-where, f95-01-sign-offs-counted-once, f12-05-service-worker-path-test]
files:
  - factory_dashboard/static/notify.js
  - factory_dashboard/static/sw.js
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
What arrives together is one notification, it carries its own title, and a tap opens the page it is about.

### Context
Read `.factory/cards/f114-i-want-to-be-notified-only.md` (D2, D3), then `factory_dashboard/static/notify.js` (`compare`, `show`), `factory_dashboard/static/sw.js`, and `notices` and `_live_context` in `factory_dashboard/overview.py`. Follow the worked examples in `tests/factory_dashboard/test_app.py`: `test_the_page_notifies_once_per_new_item_and_once_when_all_is_done` with `FAKE_NOTIFICATION`, and `test_sw_finds_open_dashboard_tab_on_notification_tap`.
- `#live-facts` carries `data-notices`: id mapped to `{"title", "body", "link"}`. `compare` reads it instead of `data-needs`.
- **One per look:** the new ids of one compare give one notification. One new item: its title, its body, its link. Several: the title "N things need you", their titles one per line as the body, the link `/planning` with the page's project kept as the item links keep it.
- "All work done" stays a notification of its own, as today.
- **The tap:** the link goes in the notification's `data` (`{ body, tag, data: { link } }`). The worker's scope is `/static/`, so it controls no page and `client.navigate` fails: in `notificationclick` it focuses an open dashboard page and sends it the link with `postMessage`; with no page open it calls `openWindow` with the link, or `/` when there is none. `notify.js` listens for that message on `navigator.serviceWorker` and goes to the link. Without a service worker, the notification's own `onclick` focuses the window and goes to the link.
- A page goes only to a link that starts with `/` and not with `//`: the message could come from elsewhere.
- **Then `data-needs` goes:** remove the attribute from `factory_dashboard/templates/_partials/live.html` and `notify` from `_live_context`, and move the tests that read `data-needs` (`_facts` in `tests/factory_dashboard/test_app.py`, and the ones in `tests/factory_dashboard/test_overview.py`) to `data-notices`, keeping what each one proves.
- What `compare` keeps in `localStorage` (the ids seen, done, the time) and the 60-second rule don't change.

### Done when
- one new item between two looks: one notification, with the item's title and body, not "Needs you"
- three new items between two looks: one notification titled "3 things need you", its body the three titles
- the next look with the same items shows nothing more
- a notification shown through the service worker's registration has `data.link`; the tests f12-05 added for that path still prove what they proved, with the new title
- a click on a notification shown without a service worker takes the page to its link
- a message `{ link: "/planning/f7" }` from the service worker takes the page there; one with `https://example.org` or `//example.org` does nothing
- `factory_dashboard/static/sw.js` posts the link to an open page and focuses it, and opens the link when no page is open
- `#live-facts` has no `data-needs`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 10233
gate_failures: ['task-tests']
tokens: 11821754
```
