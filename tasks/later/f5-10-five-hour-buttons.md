---
id: f5-10-five-hour-buttons
milestone: f5-board
depends_on: [f5-07-replan]
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Needs-you item for Claude's 5-hour window has Yes and No buttons that answer the runner's question from the dashboard.

### Context
**Replaced, not to be queued** (f5-07, 2026-10-13): ADR 22 item 4 turned the 5-hour question into a switch. The `five_hour` request this ticket posts no longer exists (`POST /requests` answers 400); the request is `reserve`, subject `five_hour`, value `on` or `off`, and its lever is on the allowance panel (f8-06, f8-14). The five-hour item names that switch in its text. The rest is kept as written, for the record.

Read `factory_dashboard/overview.py` (`Need`, `needs_you`), `factory_dashboard/templates/_partials/live.html`, `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md` ("a button that asks the runner"), and `tests/factory_dashboard/test_overview.py`.
- The item is an `owner_items` row with `kind = 'five-hour'`. Its buttons post a `five_hour` request with value `yes` or `no`. Other items get no buttons.
- The live partial refreshes every 5 s, so after a click the item shows the request partial in its place until the runner has answered and the item goes.

### Done when
- a five-hour item shows Yes and No buttons, each with its value in the request, asserted within the item
- another kind of item shows no buttons
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
