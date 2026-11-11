---
id: f77-02-one-allowance-bar
milestone: f77-the-bars-in-the-agent-allowance
difficulty: 3
depends_on: [f77-01-allowance-bars-same-width, f32-01-lead-window-resets]
files:
  - factory_dashboard/templates/_partials/allowance_bar.html
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
One macro draws an allowance window's bar, so the Overview and the planning room colour the same reading the same way.

### Context
Read `.softfield/cards/f77-the-bars-in-the-agent-allowance.md` (Notes, D1), `factory_dashboard/templates/_partials/allowance.html` (its `fill` rule and `.meter`), `#lead-window` in `factory_dashboard/templates/planning.html` (its two `.meter`s, each with its own copy of the rule), and `WindowAllowance` in `factory_dashboard/overview.py`.
- Today the planning tile has no red: a reading above 95% is red on the Overview and yellow on Planning.
- Write a macro `allowance_bar(a)` in the new `factory_dashboard/templates/_partials/allowance_bar.html` that draws one window's `<div class="meter">`: the fill (`under-mark`, `past-mark` or `nearly-out`, the Overview's rule as it is), its width, and the mark with its title when `a.mark` is set, plus whatever f9-29 added to the Overview's bar (the pace tick). Both templates `{% import %}` it and keep no fill rule of their own.
- The words around each bar (percent, reset, lever, the 75% line's sentence) stay as each page has them.
- The planning tile today falls back to a mark at 75% when there is no window; `planning` in `factory_dashboard/planning.py` always finds both Claude rows (f32-01's notes), so drop the fallback.

### Done when
- with a 5-hour reading at 97%, the bar's fill is `nearly-out` on `/` and on `/planning`; at 80% (past the mark) `past-mark` on both; at 40% `under-mark` on both
- neither `allowance.html` nor `planning.html` holds the words `under-mark`, `past-mark` or `nearly-out`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 6260
gate_failures: ['task-tests']
tokens: 6088715
```
