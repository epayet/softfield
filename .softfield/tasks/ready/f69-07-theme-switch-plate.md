---
id: f69-07-theme-switch-plate
milestone: f69-i-want-a-button-to-switch
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_app.py
area: factory
---

### Goal
The top bar's theme button becomes a compact upright switch, a moon over a sun on a small plate with a hazard-yellow knob over the theme that is on, in the Pause sign's square, instead of the word "Light" or "Night".

### Context
The picture to build: `.softfield/cards/f69-mockup/theme-switch.html` (Proposed, A, the compact switch; not B). Read `#theme-btn` and its two scripts in `factory_dashboard/templates/base.html`, `.theme-btn` and the phone top bar in `factory_dashboard/static/dashboard.css`, and the f69-01 tests in `tests/factory_dashboard/test_app.py` (from "theme switch button").
- **Markup:** keep `id="theme-btn"` and the click and system-change scripts. The button gets `role="switch"`, `aria-label="Night theme"` and `aria-checked` (`true` while night shows); it holds a plate span with a knob span and two inline SVGs, the moon and the sun, copied from the mock-up's symbols. No words inside it; its `title` stays "Switch to the light theme" / "Switch to the night theme".
- **The scripts** set `aria-checked` and the `title` where they now set the words, in both places.
- **CSS:** replace `.theme-btn` with the mock-up's `.theme-switch` rules: a clear 36 px square button holding a 24 × 36 px plate, the knob in `--hazard` at the top (night) or the bottom (light), the icon under the knob in `--hazard-ink`, the other in `--muted`; the slide only under `prefers-reduced-motion: no-preference`. Tokens only: the knob's two shading lines are the only raw `rgba`, as in the mock-up.
- **Phone:** the switch keeps its grid place on the top bar's single row: the button 44 × 44 px, the plate 24 × 40 px.
- Update the f69-01 tests that read the button's words: they check `aria-checked` instead.

### Done when
- every page's top bar has the switch: no text inside it, the moon and the sun drawn, `aria-checked` true at night and false by day
- pressing it switches the theme as before, moves the knob, and flips `aria-checked` and the `title`; the choice still sticks on reload
- a system change, with nothing stored, moves the knob too
- the switch is no wider than the Pause sign: 36 px on a wide screen, 44 × 44 px at 390 px, where the top bar is no taller than before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
