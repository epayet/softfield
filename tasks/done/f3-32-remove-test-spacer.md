---
id: f3-32-remove-test-spacer
milestone: f9-line-polish
depends_on: []
difficulty: 2
files:
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_line.py
finding: f3-31-F1
---

### Goal
The home page has no empty gap under the line: the test-only spacer is gone, and the phone replay bar still sticks to the bottom of the screen only while a replay is on.

### Context
Read `factory_dashboard/templates/overview.html` (a `<div class="spacer" style="height: 200vh;"></div>` sits before the away partial) and `test_on_a_phone_the_replay_bar_sticks_to_the_bottom_with_44_px_controls` in `tests/factory_dashboard/test_line.py`.
- f3-31 shipped that 200vh spacer in the real page, so every visitor scrolls through two screens of nothing. It was probably added so the sticky bar had something to stick over.
- The same ticket dropped the check that the bar's bottom edge meets the bottom of the screen (`abs(box["y"] + box["height"] - size["height"]) <= 1`), which the f3-07 test had. Sticky only shows at the edge when the page is taller than the screen, so the test must scroll or use a page that is, not the template.

### Done when
- a browser test at 390 px: no element in `overview.html`'s output has a 200vh height, and the page's height is its content's
- during a replay at 390 px, `#replay`'s bottom edge is within 1 px of the screen's bottom with the page scrolled to the top (the page being taller than the screen by its own content, or by content the test adds)
- before any replay and after "Back to live", `#replay` is not sticky
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 2286
gate_failures: ['stopped', 'stopped']
tokens: 1153833
```
