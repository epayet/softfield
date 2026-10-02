---
id: f4-16-allowance-mark
milestone: f4-always-on
depends_on: [f4-12-allowance-top]
difficulty: 2
files:
  - factory_dashboard/static/dashboard.css
  - factory_dashboard/templates/overview.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The reserve marks on the allowance meters ("kept for you from here", "reserve kept for the lead from here") are clearly visible in light and dark mode.

### Context
Read the `.meter` rules in `factory_dashboard/static/dashboard.css`, the `allowance` section's meter markup (now in `factory_dashboard/templates/_partials/live.html` after f4-12, or in `factory_dashboard/templates/overview.html`) and the allowance tests in `tests/factory_dashboard/test_overview.py`.
- Facts: `.meter > .mark` is a 2 px line in `var(--warn-ink)`, which in light mode is `#8a5d00` (dark brown) drawn on the orange fill (`--a2`). It can't be seen once usage passes the mark. `.meter` has `overflow: hidden`, which also cuts the mark's intended overhang (`top: -4px; bottom: -4px`).
- Draw the mark in `var(--ink)` with a 1 px `var(--surface)` outline on each side, so it reads on both the fill and the track, in both themes. Let it overhang the meter: the overflow clipping moves to the fill only.
- Give the mark a `title` with its label, so a tap or hover explains it.

### Done when
- the mark's element has a `title` equal to its label (asserted within its row)
- the CSS draws the mark in `--ink` with a `--surface` outline, and `.meter` no longer clips it (the review checks a screenshot in both themes)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
