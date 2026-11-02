---
id: f69-01-theme-button
milestone: f69-i-want-a-button-to-switch
difficulty: 3
depends_on: [f12-03-remove-review-probe, f68-02-brand-tests-check-content]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/static/charts.js
tests:
  - tests/factory_dashboard/test_app.py
area: factory
---

### Goal
A button in the dashboard's top bar switches between the light and the night theme, and the choice sticks on that device.

### Context
Read `factory_dashboard/templates/base.html` (the top bar, "Turn on notifications"), the two `prefers-color-scheme: light` blocks of `factory_dashboard/static/dashboard.css`, `draw()` in `factory_dashboard/static/charts.js` (charts read the tokens once, when drawn) and `test_dark_is_the_default_and_light_follows_the_system` in `tests/factory_dashboard/test_app.py`. Decisions are in `.softfield/cards/f69-i-want-a-button-to-switch.md`.
- **The theme is `data-theme` on `<html>`:** `light` or `dark`. A small inline script at the top of `<head>`, before the stylesheet, sets it from `localStorage` (key `theme`), else from `matchMedia("(prefers-color-scheme: light)")`, and follows a system change while nothing is stored.
- **The stylesheet:** both light blocks key on `:root[data-theme="light"]` instead of the media query; dark stays the `:root` default (and what shows without script). Tokens only, no new colours.
- **The button** sits beside "Turn on notifications" and names the theme it switches to: "Night" while light shows, "Light" while night shows, with the title "Switch to the night theme" / "Switch to the light theme". Pressing it sets `data-theme`, stores the choice and dispatches a `themechange` event on `document`.
- **Charts:** on `themechange`, `factory_dashboard/static/charts.js` redraws every drawn chart with the new colours (dispose and draw again).
- On a phone (≤ 639 px) the button adds no line to the top bar: it shares the brand's line with the project select.

### Done when
- every page's top bar has the button; pressing it switches the page to the other theme at once, charts and the floor included, without a reload
- the choice stays on reload and on the other pages; with nothing stored, the page follows the system
- `dashboard.css` has no `prefers-color-scheme` left; the light tokens still read at 4.5:1 on every plate (update the test to read `:root[data-theme="light"]`)
- at 390 px the top bar is no taller than before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 9345
gate_failures: ['task-tests']
tokens: 5907669
```
