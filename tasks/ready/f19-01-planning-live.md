---
id: f19-01-planning-live
milestone: f19-will-i-need-to-refresh-planning
difficulty: 4
depends_on: []
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
The Planning desk and an open thread refresh themselves every 5 s, so the lead's answer appears without a reload, and a refresh never wipes what the owner is typing.

### Context
Follow the Overview's live wrappers in `factory_dashboard/templates/overview.html`: a `div` with `hx-get`, `hx-trigger="every 5s [window.liveIdle()]"`, `hx-select` and `hx-swap="innerHTML"`. Here each page polls itself (`/planning{{ q }}`, or the thread's own URL) instead of `/live`.
- `factory_dashboard/templates/planning.html`: wrap `#desk-coming` and `#desk` (not the `#plant` form, not `#tiles`).
- `factory_dashboard/templates/thread.html`: refresh `#conversation`'s messages and `#waiting`, not the `#reply` form; the form's `htmx:afterRequest` script already re-fetches `#conversation`, a worked example of the fetch.
- `window.liveIdle` in `factory_dashboard/templates/base.html` waits on scroll and selection only. Make it also false while an `input` or `textarea` has focus or holds text (the owner, 2026-10-07: "a refresh sounds good", as long as a half-written reply survives).
- When the lead's answer brings a new `#reply` form, swapping it in is fine: the old one was empty.

### Done when
- `/planning` has a poll on its desk with `hx-trigger="every 5s [window.liveIdle()]"`, and none around `#plant`
- a thread's page (/planning/f19) has a poll on its messages, and the `#reply` form sits outside what it swaps
- `liveIdle` in `/`'s HTML checks focused or filled text fields as well as scroll and selection
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
