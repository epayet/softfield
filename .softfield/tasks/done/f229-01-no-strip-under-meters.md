---
id: f229-01-no-strip-under-meters
milestone: f229-in-every-loading-bar-in-overview
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
Every bar on the dashboard is one bar: the strip with four chunks under it is gone from the Overview's allowance, the planning room's lead window and the board's cards.

### Context
The picture to build: `.softfield/cards/f229-mockup/meters.html`. Decisions: D1 to D4 in `.softfield/cards/f229-in-every-loading-bar-in-overview.md`.
- The strip is the `meter-ticks` element, right after the `.meter`, in `factory_dashboard/templates/_partials/allowance.html`, `factory_dashboard/templates/planning.html` (twice) and `factory_dashboard/templates/board.html`, with its rule and comment in `factory_dashboard/static/dashboard.css`.
- With it gone the words would touch the bar, and the mark overhangs the bar by 4 px: `.meter` gets `margin-bottom: 6px`, and `.card .meter` gets `margin-bottom: 0`, since `.card`'s `gap` already spaces it.
- `.gauge` on the Agents page is a different element: leave it.
- `tests/factory_dashboard/test_app.py` has `test_gauge_has_quarter_ticks`, which asserts the strip. Replace it with the test below.

### Done when
- `/`, `/planning` and `/board` have no `meter-ticks`, with allowance readings and with a card that has tickets
- no file in `factory_dashboard/templates/` and not `factory_dashboard/static/dashboard.css` contains `meter-ticks` (a test reads them, so a later ticket can't bring it back)
- each bar's fill and mark are drawn as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1923
gate_failures: []
tokens: 1430763
```
