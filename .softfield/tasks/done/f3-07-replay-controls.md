---
id: f3-07-replay-controls
milestone: f3
depends_on: [f3-06-replay-data, f3-03-line-motion, f3-09-line-phone-fixes, f3-10-line-phone-finish]
difficulty: 6
files:
  - factory_dashboard/templates/line.html
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/static/factory.js
  - factory_dashboard/line.py
tests:
  - tests/factory_dashboard/test_line.py
---

### Goal
The factory line gets its replay bar: "Replay" (overnight or the last 24 h) loads that stretch, pauses the live floor and draws the floor as it was at the start; "Back to live" resumes the live floor. Stepping through the events is the next ticket (f3-11); here Play, ◀ ▶ and the speed are only shown.

### Context
Read the `.replay` bar in `docs/milestones/f1-factory-mockup.html` (its markup near `id="replay"`, its CSS including the `max-width` rule that makes it a sticky bar), `factory_dashboard/templates/line.html`, `factory_dashboard/templates/_partials/line.html`, `drawAll` in `factory_dashboard/static/factory.js`, `line_page` in `factory_dashboard/line.py`, and `open_line`, `night_client`, `night_db` in `tests/factory_dashboard/test_line.py`.
- **Where things live:** htmx replaces `factory_dashboard/templates/_partials/line.html` (the `#line-live` section) whole every 5 s, so the bar goes in `factory_dashboard/templates/line.html`, inside `.page`, after the include. Its styles go in `factory_dashboard/static/dashboard.css`.
- **The bar:** a Replay button with a choice of "overnight" and "last 24 h"; then Play, ◀, ▶, a speed select (every 5, 3 or 1.5 s, as the mock-up's values), a readout line and "Back to live". Only Replay shows until a replay is loaded.
- **Data:** the overnight URL is on `.page` as `data-replay`. For "last 24 h", `line_page` adds a second URL the same way (since = its local now − 24 h). Build it on the server: events come back in `since`'s zone, and a browser `toISOString()` would make them UTC. The JSON is `{since, until, line, events}`; `line` has the same shape as the `#factory-line` block. Keep the loaded JSON where f3-11 can reach it in `factory_dashboard/static/factory.js`.
- **While replaying:** the floor is drawn from the JSON's `line` (`draw`, or `drawPhone` under 640 px), and the readout says how many events there are since when, its clock taken from the `since` string's HH:MM (not a `Date`).
- **Pausing the refresh:** htmx fires `htmx:beforeRequest` on `#line-live` before each refresh, and calling `preventDefault()` on that event cancels the request. "Back to live" stops cancelling, redraws from `#factory-line` and hides the bar.
- **Tests:** `open_line` answers 404 for everything but `/line` and `/static/`; let it serve `/line/replay` from the client (path and query) so the button works in Chromium. `/line` builds `since` in the server's local zone, so expect what the route's JSON says, not fixed clocks: on this machine (+01:00) overnight is since 20:00+01:00, with 27 events.

### Done when
- a browser test on the fixture night: Replay shows the bar and draws the floor at `since` (the merged station holds `n0-01-early`, where the live floor holds `n1-03-parked`); the readout gives the count and `since`'s clock; "Back to live" hides the bar and draws the live floor again
- at 390 px wide the bar is a sticky bar at the bottom of the screen, and every button and select in it is at least 44 px wide and tall
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 562968
logs: var/runs/20261003-074205/f3-07-replay-controls
```

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 499612
logs: var/runs/20261003-132503/f3-07-replay-controls
```
