---
id: f81-02-square-parts
milestone: f81-assess-the-current-ui-state-of
agent: developer
difficulty: 2
depends_on: [f81-01-plate-panels]
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/_partials/idle_crate.svg
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The dashboard's small parts are angular like the rest of the floor: square tags with a square lamp, no rounded corners anywhere, an empty panel shows an idle crate, and a meter sits in a slot with a gauge's quarter ticks under it.

### Context
Build the tags, the empty state and the meter of the Proposed side of `.softfield/cards/f81-mockup/theme-pass.html` (`.prop .pill`, `.idle`, `.prop .meter`, `.gauge`); card doc `.softfield/cards/f81-assess-the-current-ui-state-of.md` D2–D3.
- `.pill` in `factory_dashboard/static/dashboard.css`: square, mono capitals, a square lamp; `--dot` keeps its meaning (the colours that say good, warn, running stay as they are).
- Remove every `border-radius` in `dashboard.css` (the crate card and its phone sheet, `.empty`, `.new-version`, `.factory-status .sign`, the crate card's close button, `code`); keep the round status dot of the top bar, which is a light, not an ornament.
- `.empty` shows the idle crate: one inline SVG partial, `factory_dashboard/templates/_partials/idle_crate.svg`, drawn in `currentColor`, beside the words. Include it from the templates that print `class="empty"` (search them), words unchanged.
- The meter's slot and the gauge are CSS only (`.meter` and a `::after` or a sibling `.gauge`), in `--rule` and `--floor`; the mark and fill colours stay.

### Done when
- no `border-radius` in `dashboard.css` but the top bar's status dot
- a page with an empty panel shows the idle crate beside its words
- tags are square with a square lamp, colours as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 3186
gate_failures: []
tokens: 4654537
```
