---
id: f81-01-plate-panels
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 3
depends_on: []
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
Every dashboard panel is a plate: a striped plate header and corner ticks, as the card page's "What it's about" already is, on a floor with a faint grid.

### Context
Read `.factory/cards/f81-assess-the-current-ui-state-of.md` (D1–D3) and build the panels of the Proposed side of `.factory/cards/f81-mockup/theme-pass.html` (its `.prop .panel` rules), without the readouts, tags, belt or buttons (later tickets).
- The example to follow is `.about` in `factory_dashboard/static/dashboard.css` (plate header, `.stripe`, corner ticks via `::before`/`::after`).
- Add the tokens `--tick`, `--stripe` and `--notch` at the top of `dashboard.css` beside the others, in the dark `:root` and, where they differ, in `:root[data-theme="light"]`; move `.about` and `.aside` onto `--tick` and `--stripe`.
- `.panel > h2` becomes the plate header for every page that uses `.panel`; the stripe is the `h2`'s own `::after`, so no template changes. `.panel.needs > h2` is the hazard-yellow plate. Panels whose first child is not an `h2` keep their top padding.
- `factory_dashboard/templates/_partials/queue.html`'s title `<h3>Queue</h3>` becomes an `<h2>` like the other panels; the "Next in line" `h3` stays.
- The faint grid is the `body`'s background in `--grid`, 32 px.
- Ornament uses `--tick`, `--rule` and the hazard stripe only, and has no animation.

### Done when
- every `.panel` with an `h2` shows the plate header and the two corner ticks, in both themes
- "Needs you" shows the yellow plate
- the Queue panel's title is an `h2`
- `.about` and `.aside` look as before, on the new tokens
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 2707
gate_failures: ['all-tests', 'protected-paths']
tokens: 2912184
```
