---
id: f254-01-allowance-rows-on-a-phone
milestone: f254-on-mobile-each-allowance-box-take
difficulty: 3
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/allowance.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On a phone, the Overview's Agent allowance shows each window as a compact row instead of a tall box, with every word kept.

### Context
The picture to build is `.softfield/cards/f254-mockup/allowance-phone.html`, Proposed (without its green outlines and notes). Read D1–D3 in `.softfield/cards/f254-on-mobile-each-allowance-box-take.md`.
- The phone rules today: the `@media (max-width: 639px)` block after `.allow` in `factory_dashboard/static/dashboard.css` (f9-17). Change them there; the rules outside it stay as they are.
- The template: `factory_dashboard/templates/_partials/allowance.html`. A wrapper around the name and the reading is fine if the phone layout needs one; keep each window's `id="allow-…"` and the lever's attributes as they are.
- The existing allowance tests read the rows by their id (`allowance_rows` in `tests/factory_dashboard/test_overview.py`); follow the browser tests at 390px in that file for the new one.

### Done when
- at 390px wide, with readings for Claude's two windows and Copilot's month, the three windows together are at most 280px tall (a browser test)
- at 390px wide, no window has a border or a background of its own, and windows are split by a thin rule
- at 390px wide, the name, the percent and the meter sit in the same band as the "use reserve" lever, and the lever is still at least 44px tall
- at 390px wide, the reset, read and mark words of a window share lines, and "at this rate" keeps a line of its own
- at 1440px wide, each window is drawn as before (same text, same order, the windows side by side as today)
- every word the allowance shows today is still in the page, at both widths
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
