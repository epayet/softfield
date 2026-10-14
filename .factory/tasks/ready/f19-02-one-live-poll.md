---
id: f19-02-one-live-poll
milestone: f19-will-i-need-to-refresh-planning
difficulty: 3
depends_on: [f19-01-planning-live, f9-28-allowance-live]
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview refreshes its live parts from one `/live` request every 5 s instead of one per part.

### Context
Read `factory_dashboard/templates/overview.html`: `#live-needs-you`, `#live-now`, `#live-queue` (and `#live-allowance`, added by f9-28) each fetch the same `/live{{ q }}` every 5 s, and the top bar's `#live-poll` in `factory_dashboard/templates/base.html` fetches it too: four or five renders of one page per poll.
- Keep one poller on the Overview, with `hx-trigger="every 5s [window.liveIdle()]"`, `hx-swap="none"` and `hx-select-oob` naming each part (`#needs-you:#live-needs-you`-style pairs, innerHTML), so each wrapper keeps its id and Needs you still comes back after an empty spell (f3-16).
- The top bar's poll stays as it is on other pages; on the Overview the single poller updates `#live-facts` too.

### Done when
- `/` has exactly one element with `hx-get="/live…"`, and it updates Needs you, Now, Queue, the allowance and the top bar's facts
- other pages keep the top bar's own poll
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
