---
id: f81-09-send-order-keeps-its-colour
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 1
finding: f81-08-wire-square-parts
depends_on: []
files:
  - factory_dashboard/templates/projects.html
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The "Send new order" button on the Projects page is hazard yellow again when it can be pressed, and stays the plate colour while it is disabled.

### Context
f81-08 removed `background: var(--hazard); color: var(--hazard-ink)` from `.projects-page .send-order` in `factory_dashboard/static/dashboard.css`, on the reasoning that `.btn.go` supplies them. The button in `factory_dashboard/templates/projects.html` (line 59) is `class="send-order btn"`: it has `btn` but not `go`, so no rule gives it a background any more, and `.send-order:disabled` is the only colour left.
- The same change dropped the same declarations from `.order-bar .go` and `.aside .go`; those buttons do carry `btn go` (see the `go btn` buttons in the board and ticket templates), so they are fine.
- Add `go` to the button's classes. `.btn.go:disabled` is a dashed outline, while `.projects-page .send-order:disabled` sets a plate fill; check which wins and keep the disabled look the page had.
- Test: read `projects.html`'s rendered button and assert its class list contains `btn` and `go` (content, not the CSS text alone).

### Done when
- the rendered "Send new order" button carries both `btn` and `go`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1628
gate_failures: []
tokens: 882026
```
