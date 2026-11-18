---
id: f266-01-stripe-covers-the-fill-to-its-end
milestone: f266-there-s-a-tiny-green-dot
agent: developer
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/_partials/allowance_bar.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
When the week is over pace, the hazard-striped stretch ends exactly where the meter's green fill ends, so no sliver of green shows to its right.

### Context
Read D1 in `.softfield/cards/f266-there-s-a-tiny-green-dot.md`, then the `allowance_bar` macro in `factory_dashboard/templates/_partials/allowance_bar.html` and the `.meter > span` rules in `factory_dashboard/static/dashboard.css` (the fill starts 1px in from the meter's edge; the stripe's inline `left` drops that 1px). Follow `test_over_pace_the_week_shows_the_post_the_stripes_and_the_plate` in `tests/factory_dashboard/test_overview.py` and its twin near line 3219 in `tests/factory_dashboard/test_planning.py`; `pace_client` there sets the week's use.

### Done when
- the macro rounds the fill's width and the post's place to whole percents once each, and the stripe uses those same two numbers: it starts at the post's percent plus 1px (`left:calc(33% + 1px)`) and its width is the fill's percent minus the post's (`width:32%`), so its right edge is the fill's right edge
- a new test picks `used` and `resets_in` for `pace_client` so that rounding `used - post` alone gives one percent less than the rounded fill minus the rounded post (the live case on 2026-11-18: 0.357 used, line 0.264, fill `width:36%`, post `left:26%`, stripe `width:9%`), and checks the stripe's width is the fill's percent minus the post's
- the post (`class="pace"`), the fill's colour and the meters of other windows are unchanged; the CSS is not touched
- the two existing over-pace tests expect the new `left:calc(…)` style
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 3529
gate_failures: ['stopped']
tokens: 1805587
```
