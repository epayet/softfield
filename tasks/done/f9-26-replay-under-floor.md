---
id: f9-26-replay-under-floor
milestone: f9-line-polish
depends_on: [f9-13-home-without-clog-and-verdict]
difficulty: 2
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_line.py
---

### Goal
On the Overview, the replay bar comes right after the floor, not at the bottom of the page under the charts.

### Context
Read `factory_dashboard/templates/overview.html` (`{% include "_partials/line.html" %}`, and `#replay` after `#spend`: its comment says why it sits outside `#line-live`), the `.replay` rules in `factory_dashboard/static/dashboard.css` (it sticks to the bottom only while replaying, f3-31), the section-order test in `tests/factory_dashboard/test_overview.py`, and `test_on_a_phone_the_replay_bar_sticks_to_the_bottom_with_44_px_controls` in `tests/factory_dashboard/test_line.py`.
- The owner (2026-10-06): "the replay bar should be just below the factory line on mobile". The same place on desktop is fine.
- It must stay outside `#line-live`, which htmx refreshes every 5 s.
- The sticky-to-the-bottom rule (f3-31) was there because the bar sat below the charts, off screen while watching the floor. `position: sticky; bottom: 0` only ever moves an element up from where it would sit, never down, so once the bar is right under the floor (on screen at the top of the page) it can't stick to the bottom any more and the f3-31 test fails. Under the floor the bar is already on screen with it, so the sticky is no longer needed: drop the sticky positioning and its shadow on a phone, keep the 44 px controls and the safe-area padding, and fix the comment above the `.replay` rules.
- `.page` already spaces panels 14 px apart; no margin tweak is needed to meet the 40 px gap.

### Done when
- `#replay` is the next element after `#line-live` in `/`, and still outside it
- at 390 px the replay bar's top is within 40 px of the floor's bottom
- the section-order test lists the new order
- the f3-31 phone test in `test_line.py` says what's true now: at 390 × 844, while replaying, the whole bar is on screen at the top of the page and every control is at least 44 px (it no longer asserts sticky, nor that the bar's bottom meets the screen's bottom)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 9667
gate_failures: ['all-tests', 'all-tests']
tokens: 6449692
```
