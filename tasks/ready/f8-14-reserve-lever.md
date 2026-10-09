---
id: f8-14-reserve-lever
milestone: f8-one-queue
depends_on: [f8-06-switch-buttons, f9-28-allowance-live]
difficulty: 3
files:
  - factory_dashboard/templates/_partials/allowance.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Each Claude meter's reserve switch is a small factory lever on the meter's own line, labelled "use reserve", instead of a sentence and a button on a line of their own.

### Context
The owner (2026-10-09): "I like the switches but the labels take a bit of space on mobile. I also wonder how to make the button a bit more fun in the theme?" The picture is `docs/milestones/f8-mockup/reserve-lever.html` ("Proposed"): copy its `.lever` CSS into `factory_dashboard/static/dashboard.css` in place of the `.allow .switch` rules, using the tokens already there.
Read the switch in `factory_dashboard/templates/_partials/allowance.html` (from f8-06; f9-28 moves the legend to the panel's bottom) and the switch tests in `tests/factory_dashboard/test_overview.py` (`switch_row` and the tests after it).
- **The lever** is the `button` that posts today's `reserve` request, unchanged: same `hx-post`, `hx-vals` and `hx-on::before-request`, except the latter no longer removes the button. It now adds `on-its-way` to the button and disables it. It carries `role="switch"`, `aria-checked` (`true` when `sw.until`), and `aria-label` and `title` equal to `sw.label` (`SWITCHES` in `runner/loop.py`). Its visible words are "use reserve", then a lamp and the slot with its knob.
- **Where:** in the meter's first `.line`, after the percent. The switch's own row (`div.switch`) goes.
- **On:** the knob slides right, the slot shows hazard stripes and the lamp lights; "on until Sat 09:30" (`sw.until`) shows in the second `.line` in place of the mark's label, in `--hazard`.
- **Asked** (`sw.asked`): the lever is rendered disabled with `on-its-way`: knob halfway, a dashed `--hazard` edge, the lamp blinking. Its `title` reads "asked: on" or "asked: off".
- The lever keeps a 44 px tap height; the knob's slide and the blink stop under `prefers-reduced-motion`.
- **The legend** ("How to read the allowance") gains two lines from the mock-up: "use reserve: let the factory work past the mark; on lasts 24 hours, then turns itself off" and "halfway, with a dashed orange edge: a lever you pulled, on its way to the runner". The second replaces today's "a dashed orange edge: a switch you turned…".
- Rework `switch_row` to find the row's `button[role="switch"]` and return its `aria-label`, `aria-checked`, the row's "on until"/"asked" words and its `hx-vals`; keep each test's meaning.

### Done when
- each Claude meter row has one `role="switch"` button in its first line, `aria-checked` matching the stored state, `aria-label` equal to its `SWITCHES` sentence, and its request carrying the right subject and value (asserted within that row)
- an on switch's row shows "on until" and its time; an off one doesn't
- an asked switch is disabled with class `on-its-way` and says "asked: on" in its `title`
- a meter of another agent has no switch; the row has no `div.switch` left
- the legend holds the "use reserve" line
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
