---
id: f256-01-top-row-in-line
milestone: f256-the-alignments-of-the-top-bar
difficulty: 2
depends_on: [f194-01-four-slot-menu]
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
On a wide screen the top bar's top row is one line: every part centred on the same line, every control the same height, its left and right edges on the stripe's, and a narrower window shortens the status words instead of wrapping the row.

### Context
Read `.softfield/cards/f256-the-alignments-of-the-top-bar.md` (D1 to D4) and build the Proposed of `.softfield/cards/f256-mockup/top-bar.html`: its CSS under "PROPOSED" is the picture to copy, on the tokens of `factory_dashboard/static/dashboard.css`.
- `factory_dashboard/static/dashboard.css`: the top bar's rules (`.bar-top`, `.brand`, `.factory-status` and its `.sign` and `.uptime`, `.filters`, `.theme-switch`) and the phone block `@media (max-width: 639px)`. `--control-h: 36px` joins the tokens at the top of `:root`. The phone's bar keeps its look: its grid, its 44 px switch and sign, its hidden words; hide the picker's new `.key` there.
- `factory_dashboard/templates/base.html`: the `filters` form in `.bar-top` (f194-01 put it back there). Wrap "Project" in `<span class="key">`; keep the select's `name`, `onchange` and the `<noscript>` button.
- The tabs are f194-01's four slots: don't change them.
- `tests/factory_dashboard/test_app.py` drives the real page with Playwright: `test_at_390px_the_top_bar_is_no_taller` shows the routing and measuring with `getBoundingClientRect`. Measure the parts, not the stylesheet's text.

### Done when
- at 1440 px and at 1000 px, in both themes, the vertical centres of the brand, the dot, the sign, the "On" plate, the picker and the theme switch are within 1 px of each other, and the sign, the "On" plate, the picker and the switch are the same height
- at 1440 px the logo's crate's left edge is within 1 px of the hazard stripe's left edge, and the switch's right edge within 1 px of the stripe's right edge
- at 760 px the top row is one line (its height is what it is at 1440 px) and the status words end in "…", the dot's title still holding the whole sentence
- at 390 px the top bar is no taller than before and the picker shows only the project's name
- choosing a project in the picker reloads the page with it, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 1948085
logs: .softfield/var/runs/20261120-174051/f256-01-top-row-in-line
```
