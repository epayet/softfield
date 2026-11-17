---
id: f259-01-planning-week-pace
milestone: f259-the-pace-indicator-is-only-on
difficulty: 3
depends_on: []
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/_partials/allowance_bar.html
  - factory_dashboard/templates/_partials/allowance.html
tests:
  - tests/factory_dashboard/test_planning.py
---

## Goal
The Planning room's week bar, in "The lead's window" tile, shows Claude's week pace as the Overview does: the dashed post, the striped stretch over it, and the same "Over pace" or "Last hours" plate under it.

## Context
- The picture to build: `.softfield/cards/f259-mockup/planning-week-pace.html` (Proposed).
- The tile: `factory_dashboard/templates/planning.html` (`#lead-window`), filled by `planning` in `factory_dashboard/planning.py`, which passes `window` and `week` but no pace.
- The pace: `claude_pace` in `factory_dashboard/overview.py`; its `.week` is the `WeekPace` the Overview passes as `pace` (see `_live_context` there, key `"pace"`). Call it once in `planning` and pass it as `pace`.
- The bar already draws the post and stripes when given a pace: `allowance_bar(a, pace)` in `factory_dashboard/templates/_partials/allowance_bar.html`.
- F259 D1: the "Over pace" and "Last hours" plates move from `factory_dashboard/templates/_partials/allowance.html` into a macro `pace_plate(wp)` in `factory_dashboard/templates/_partials/allowance_bar.html`; both pages call it, so their words can't drift. The Overview's output stays the same: its tests in `tests/factory_dashboard/test_overview.py` (`test_over_pace_the_week_shows_the_post_the_stripes_and_the_plate` and the three after it) must pass unchanged.
- F259 D2: on Planning, "on pace · today's 22%" joins the week's small line (`week 29% · resets on … · on pace · today's 22%`); the plate goes under that line.
- Example for the tests: `pace_client` in `tests/factory_dashboard/test_overview.py` seeds a week reading; build the same for `/planning` in `tests/factory_dashboard/test_planning.py`.

## Done when
- At 65% used on a 33% pace line, `/planning`'s week bar has `class="pace" style="left:33%"` and `class="over-pace" style="left:33%;width:32%"`, and the tile shows "Over pace lead tickets wait until about …" with "developers, planning, reviews and the fast lane go on · today's pace 33%".
- At 30% used, the week bar has the post, no stripes and no plate, and the week's small line ends "on pace · today's 33%".
- In the week's last hours there is no post, and the "Last hours" plate shows as on the Overview.
- With the week's reserve lever on, there is neither post nor plate.
- The 5-hour window's bar on `/planning` never gets a post.
- The Overview's pace tests pass unchanged.
