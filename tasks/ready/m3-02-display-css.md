---
id: m3-02-display-css
milestone: 3
depends_on: [m3-01-display-page]
files:
  - coucou/static/coucou/css/display.css
tests:
  - tests/integration/test_display_css.py
max_diff: 120
---

### Goal
Style the display: calm, full screen, readable from across a room.

### Context
`coucou/static/coucou/css/display.css` only has the `[hidden]` rule. The page is `coucou/templates/coucou/display.html`:
- `<main id="display">` holds three `data-state` sections, `#offline` and `#floats`.
- The `moment` section holds `#moment-photo` (an `<img>`), `#moment-note` (a `<p>`) and `#reactions`, which is filled with `<button>`s, one emoji each.
- `coucou/static/coucou/js/render.js` adds the class `entering` to the `moment` section for 600 ms when a new moment arrives. It adds `<span class="float">` inside `#floats` for 2.5 s when someone reacts.

The look:
- **Background and fonts:** a dark, warm background (`#1c1b1a`) and soft light text. System fonts only (`system-ui`), with no web fonts.
- **Photo:** it fills the screen without cropping (`object-fit: contain`), and the note sits below it.
- **Note:** large, about `2.5rem`, centred, with generous line height.
- **Reaction buttons:** big and round with no border, at least `2rem` emoji and a subtle background. They sit in a row at the bottom.
- **`.entering`:** fades in over 600 ms.
- **`.float`:** rises from the bottom and fades out over 2.5 s. Absolutely positioned inside a fixed, full-screen `#floats` that ignores taps (`pointer-events: none`).
- **`#offline`:** small and discreet, in a corner.
- **Reduced motion:** with `prefers-reduced-motion: reduce`, no animations.

### Pattern to follow
`coucou/static/coucou/css/pair.css`

### Steps
1. Write the rules in `coucou/static/coucou/css/display.css` so every test in `tests/integration/test_display_css.py` passes, following the look above.
2. **Keep the `[hidden] { display: none !important; }` rule first: the page relies on it to show one section at a time.**

### Done when
- the listed `tests:` pass
- the full unit + integration suite passes
- all gates pass (see `docs/workflow.md`)
