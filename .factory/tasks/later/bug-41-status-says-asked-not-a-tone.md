---
id: bug-41-status-says-asked-not-a-tone
milestone: bugs
difficulty: 3
depends_on: []
area: factory
priority: 69
finding: f17-tighter-running-and-pause-presence-in-F3
files:
  - factory_dashboard/app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar's `Status` says whether the owner's request is on its way (`asked: bool`), and hands out no colour it no longer draws.

### Context
Read `class Status`, `factory_status` and `factory_wide_status` in `factory_dashboard/app.py`, and `_bar` in `tests/factory_dashboard/test_app.py`.
- Since F17 the top bar's words have no colour: `Status.tone` is read only for "asked" (the dashed edge, and `factory_wide_status`'s rank), while `factory_status` still hands out "good", "warn" and "serious".
- Replace `tone` with `asked: bool`; `_bar` changes with it. Grep the templates for `tone` before removing it.

### Done when
- a pause asked and not yet taken: the bar has its dashed edge, as today
- `factory_wide_status` still ranks an asked status first
- no template or test reads `tone`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
