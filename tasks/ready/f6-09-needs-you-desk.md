---
id: f6-09-needs-you-desk
milestone: f6-planning-room
depends_on: [f6-06-desk-page, f5-12-notifications]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Needs you and the top bar tell the owner when the desk has something for them, from the same list as the desk.

### Context
Read D6 in `docs/milestones/f6-planning-room.md`, `factory_dashboard/planning.py` (the desk's items, f6-06), `factory_dashboard/overview.py` (`needs_you`), `factory_dashboard/templates/_partials/live.html` and `factory_dashboard/templates/base.html`.
- **Needs you** gains one entry when the desk has items: "N things wait for you on your desk", the top three as links, and "Open your desk ›". Other Needs-you items stay.
  - `needs_you` already lists each open owner item, and every lead reply raises one of kind `planning` ("The lead answered your message on F7…"). Those are the desk's "answers wanted", so the desk entry replaces them: no `planning` item shows on its own.
- **The top bar's Planning tab** (added by f6-06) reads "Planning · N" when N > 0, from the same count, refreshed with the live partial.

### Done when
- with three desk items, Needs you shows the count and three links, and the tab reads "Planning · 3"
- with one lead reply unanswered, Needs you shows it once, in the desk entry, and no separate `planning` item
- with none, there's no desk entry and the tab reads "Planning"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
