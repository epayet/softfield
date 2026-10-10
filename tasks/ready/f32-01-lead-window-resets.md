---
id: f32-01-lead-window-resets
milestone: f32-the-5-hour-lead-s-window
depends_on: [f9-28-allowance-live, f12-03-remove-review-probe]
difficulty: 2
files:
  - factory_dashboard/templates/planning.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
Each row of the planning room's lead window says when its window resets, or why it has no reading.

### Context
Read `#lead-window` in `factory_dashboard/templates/planning.html` (its 5-hour row, and the week row f9-28 added), `planning` in `factory_dashboard/planning.py`, and `WindowAllowance` and `_reset_label` in `factory_dashboard/overview.py`.
- Each row's `WindowAllowance` already holds `reset_label` ("resets at 17:00", "resets on Oct 9 12:00") and `status` ("reset since, no new reading", "no data yet"); at most one of the two is set. Print whichever is set after the row's percent, joined with " · ", as the Overview's `#allowance` rows do (in `factory_dashboard/templates/overview.html`, or the partial f9-28 moved them to).
- Words only from those two fields: no new strings.
- The existing assertion on "5-hour window 80% · planning may go past the 75% line" will change with the new text; keep the 75% line's sentence in the tile.

### The branch so far (the lead read it, 2026-10-10)
Your branch already holds the whole change: both rows in the template print their reset or status, and the tests cover today's reset, a later day's (on the week row), a past reset and no reading. Don't start again and don't re-read everything.
- The `layout` gate failed on `tests/factory_dashboard/test_probe_tmp.py`. That file was never yours: a review left it on main. This ticket now waits for the ticket that removes it (f12-03), so that gate is clean when you start. Don't touch that file.
- `test_the_lead_window_shows_reset_when_not_past` asserts the same line as `test_the_lead_window_shows_the_75_line` now does: keep one of the two.
- The past-reset and no-reading tests only look for the status words anywhere in the tile. Assert the whole row instead, from its name to its status, so each proves which row said it (the percent is "–" when there is no reading).
- The full `check-all` runs the whole test suite and takes several minutes: it is slow, not stuck. Run the listed test file first, then `check-all` once, and wait for it.

### Done when
- with a 5-hour reading at 80% resetting later today at 17:00, `#lead-window` reads "5-hour window 80% · resets at 17:00"
- a reset on a later day reads "resets on <Mon> <d> <HH:MM>" on that row
- the week row shows its own reset the same way
- with the 5-hour reset already past, the row reads "reset since, no new reading"; with no reading, "no data yet"
- the tile still says "planning may go past the 75% line, the factory stops there"
- assert within `#lead-window`, on its text with tags stripped and entities unescaped (`_text` in `tests/factory_dashboard/test_planning.py`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
