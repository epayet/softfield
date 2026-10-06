---
id: f9-14-away-span-in-place
milestone: f9-line-polish
depends_on: [f3-32-remove-test-spacer]
difficulty: 4
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/templates/_partials/away.html
  - factory_dashboard/static/factory.js
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Choosing another stretch in the replay bar redraws "While you were away" and the replay's span in place, without reloading the page.

### Context
Read the span choices in the route in `factory_dashboard/overview.py` (`spans`, `choices`, the `since` cookie), `factory_dashboard/templates/_partials/away.html`, the `#replay-span` handler in `factory_dashboard/static/factory.js` (today `location.href = …`, f3-21) and the `.page` element's `data-replay` in `factory_dashboard/templates/overview.html`. The live panels' `hx-get`/`hx-select` there are the pattern to follow.
- The owner (2026-10-06): "when i click on a certain timeline, it refreshes the page".
- The address bar still gets `?since=` (a reload keeps the stretch), and choosing a span still doesn't count as looking again (f3-F3: no cookie).
- The replay then plays the new stretch.

### Done when
- a browser test: choosing "the last hour" changes `#away`'s "since" time, keeps a value set on `window` before the change, and puts `since` in the address
- Replay after the change asks `/line/replay` for the new `since`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
