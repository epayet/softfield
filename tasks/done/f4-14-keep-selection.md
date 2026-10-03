---
id: f4-14-keep-selection
milestone: f4-always-on
depends_on: [f4-12-allowance-top]
difficulty: 2
files:
  - factory_dashboard/templates/_partials/live.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview stops refreshing its live part while the owner has text selected, so a selection isn't lost every 5 s.

### Context
Read `factory_dashboard/templates/_partials/live.html` and the live tests in `tests/factory_dashboard/test_overview.py`.
- Facts: `#live` polls with `hx-trigger="every 5s"` and `hx-swap="outerHTML"`, which replaces the whole block, and any selection in it, on every poll.
- htmx (vendored, 2.0.11) supports a filter on a trigger: `every 5s [<a JavaScript expression>]` polls only when the expression is true. Use it to skip a poll while `window.getSelection()` holds any text. Skipped polls resume by themselves once the selection is cleared. No new script file.

### Done when
- the `#live` element's `hx-trigger` keeps polling every 5 s, with a filter that is false while text is selected (assert the attribute's value)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
note: done directly by the lead on 2026-10-03, with the queue's scroll (base.html's liveIdle)
```
