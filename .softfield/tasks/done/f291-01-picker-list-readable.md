---
id: f291-01-picker-list-readable
milestone: f291-the-project-picker-list-textbox-is
difficulty: 1
files:
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar's project picker, opened, lists the projects in the theme's ink on the theme's plate, in both themes, instead of light grey on the browser's white.

### Context
- The cause is in `factory_dashboard/static/dashboard.css`, the rule `.bar-top .filters select` (added by f256-01): it sets `background: transparent` so the select shows the label's plate behind it. The select's text is `var(--ink)`, a light grey in the dark theme, but a browser draws the opened list on the select's own background, and a transparent one falls back to white: light grey on white.
- Fix it in that rule's place: give the select `background: var(--plate)` (the label around it is already `var(--plate)`, so the closed picker looks the same), and add a rule for its `option`s with `background: var(--plate)` and `color: var(--fg)`, so the list follows the theme in both. Tokens only, no new colour.
- Other selects already sit on `var(--plate)` (the rule `select, input[type=search], button` just below); leave them alone.
- `tests/factory_dashboard/test_app.py` drives the real page with Playwright: `test_at_390px_the_top_bar_is_no_taller` shows the routing and the theme switch; read computed styles with `getComputedStyle`, not the stylesheet's text.

### Done when
- in the dark theme, the picker's options' computed background is the `--plate` colour and their colour the `--fg` colour, and the select's own background is not transparent
- the same in the light theme, with the light theme's `--plate` and `--fg`
- the closed picker looks as it does now: same height and width as before, measured at 1440 px and 390 px
- choosing a project in the picker reloads the page with it, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1655
gate_failures: []
tokens: 2524636
```
