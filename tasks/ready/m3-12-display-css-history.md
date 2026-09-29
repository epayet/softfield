---
id: m3-12-display-css-history
milestone: 3
depends_on: []
files:
  - coucou/static/coucou/css/display.css
tests:
  - tests/integration/test_display_css.py
max_diff: 90
---

### Goal
Style the display's new pieces calmly: the arrows, the byline, the reaction summary, names on floating emoji, the "New" hint and the settings cog with its panel (ADR 09).

### Context
`coucou/static/coucou/css/display.css` styles `coucou/templates/coucou/display.html`: a dark, calm, full-screen display read from across a room. The reaction buttons are fixed at the bottom (`#reactions`), and `#moment-note` uses `font-size: 2.5rem`.

The new elements:
- `#moment-byline` (who posted and when) and `#reaction-summary` ("❤️ Maman · 😂 Kitchen"), both under the note, inside `section[data-state="moment"]`
- `#nav-older` (‹) and `#nav-newer` (›): buttons
- `#new-hint`: a button, "New ›"
- `#settings-open`: a small ⚙ button, always there; `#settings`: its panel, with three buttons
- `.float` now holds `.float-emoji` and `.float-by` (a name)

What the screen should feel like:
- **Arrows:** at the left and right edges, vertically centred, big enough to tap, quiet (low opacity, no background), and well away from the reaction buttons at the bottom.
- **Byline and summary:** smaller and quieter than the note. The summary stays on one line and ends in "…" when too long.
- **The cog:** small and faint, in a top corner. The panel sits in front of the moment, centred, readable, with comfortable buttons.
- **"New ›":** a small pill in a top corner, in front of the moment.
- **A float's name:** below its emoji, smaller.

### Pattern to follow
The existing rules in `coucou/static/coucou/css/display.css` (colours, `rem` sizes, the `#offline` corner line).

### Steps
1. Add rules for each element above to the end of `coucou/static/coucou/css/display.css`. Use `rem` for font sizes.
2. Arrows: `position: fixed; top: 50%;` with `left` for `#nav-older` and `right` for `#nav-newer`, font size at least `2rem`.
3. `#reaction-summary`: `white-space: nowrap; overflow: hidden; text-overflow: ellipsis;` and a width limit.
4. `#settings-open`: `position: fixed`, `top` and a side, and an `opacity` below 1. `#settings` and `#new-hint`: `position: fixed` with a `z-index`.
5. **Change no existing rule: the existing tests check them.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
