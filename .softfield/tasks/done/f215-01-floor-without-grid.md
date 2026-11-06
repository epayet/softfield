---
id: f215-01-floor-without-grid
milestone: f215-i-m-not-a-fan-of
agent: developer
difficulty: 1
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The dashboard's page background is one flat colour: the lines every 32 px are gone, in both themes.

### Context
The picture to build is "Proposed" in `.softfield/cards/f215-mockup/floor.html`.
- In `factory_dashboard/static/dashboard.css`, the `body` rule (about line 77) draws the grid: remove its `background-image` (both gradients) and `background-size`. Keep `background-color: var(--bg)`.
- Keep the `--grid` token in both themes: many rules use it as a hairline colour.
- In `tests/factory_dashboard/test_app.py`, `test_body_has_the_faint_grid` holds the grid. Rename it `test_body_has_no_grid` and make it assert the body rule has neither `background-image` nor `background-size`, and still has `background-color`.

### Done when
- the `body` rule has a background colour and no background image
- `--grid` is still defined in both themes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1352
gate_failures: []
tokens: 275544
```
