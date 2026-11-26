---
id: f281-01-one-row-on-wide
milestone: f281-on-desktop-for-the-new-menu
difficulty: 3
depends_on: []
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_app.py
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
From 640 px up, the top bar's menu shows Overview, Planning and Board, then as many of the other seven pages as the window fits, and More holds only the rest; when all seven fit, More goes.

### Context
Read `.softfield/cards/f281-on-desktop-for-the-new-menu.md` (D1 to D4) and build the Proposed of `.softfield/cards/f281-mockup/one-row.html`: its CSS under "proposed" and its `#fit-nav` markup are the picture, on the tokens of `factory_dashboard/static/dashboard.css`. The mock-up's script only stands in for the window width: the dashboard does the steps in CSS (`@media (min-width: …)`, card D2), with no script.
- `factory_dashboard/templates/base.html`: `nav.tabs.slots` and its `more_pages` list (lines 200-215). Draw the seam and the seven row links from that same list, each with `?project=` (`{{ q }}`), `aria-current` when it is the page, its words as `title`, and its index (1 to 7) for the CSS; the sub-menu links carry the same index. `#planning-tab` keeps its id. Don't put the `hidden` attribute on `details.more`: `dashboard.css` line 1679 makes `[hidden]` `display: none !important`, which no step can undo. The fourth-slot naming (F194 D4) must only name and light a page that is hidden from the row at that width, so do it in CSS too (for example both labels in the summary and the current page's index on it, the right label and colour shown per step), not in the template alone.
- `factory_dashboard/static/dashboard.css`: the slots are lines 187-217 (`nav.tabs.slots > a` already matches the new row links, so they show at every width until a rule hides them); the phone's under 640 px (lines 565-569) don't change, so under 640 px the seam and the seven row links are hidden and More is the fourth slot. The script in `base.html` that closes the sub menu on a tap outside or Escape stays.
- `tests/factory_dashboard/test_app.py`: F194's slot tests use `SLOTS` and `_SLOT_BOXES` (search for them). `DISPLAY` is 1280 px wide and is used by many other tests: don't change it. At 1280 px the bar now shows ten slots and no More, so give the four-slot checks that ran at `DISPLAY` a 645 px window instead: from 640 to 649 px the row is Overview, Planning, Board, the seam, More, which is F194's four slots. Add the new checks below them. `SLOTS` must count only visible slots.

### Done when
- at 1280 px the row reads Overview, Planning, Board, then Projects, Tickets, Jobs, Runs, Timeline, Agents, Bench, at the widths of the card's D1, with the striped seam after Board, and no More is visible
- at 900 px the row ends Projects, Tickets, Jobs, Runs, More, and More's open plate lists exactly Timeline, Agents, Bench; at 645 px it is Overview, Planning, Board, More with all seven in the plate
- at each step of D2 (650, 750, 830, 900, 1010, 1070 px) and 1 px below it, nothing in the bar reaches past the window
- at 1280 px and at 900 px each slot's left edge is the same on Overview, Planning, Board and Timeline, and when the Planning count goes from 1 to 12
- on Timeline at 1280 px the Timeline slot is hazard yellow and More is not shown; on Timeline at 900 px More is hazard yellow and reads "Timeline"; on Projects at 900 px Projects is yellow in the row and More reads "More" and is not yellow
- each of the seven row links keeps the `?project=` and has its few words as `title`
- on a 390 px and a 360 px phone the bar is exactly F194's four slots and sub menu, and their existing tests still pass
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 604841
logs: .softfield/var/runs/20261125-034732/f281-01-one-row-on-wide
```
