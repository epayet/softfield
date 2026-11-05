---
id: f194-01-four-slot-menu
milestone: f194-the-menu-is-a-bit-weird
difficulty: 4
depends_on: [f132-08-picker-in-the-tabs]
files:
  - factory_dashboard/templates/base.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_board.py
  - tests/factory_dashboard/test_planning.py
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_projects.py
tests:
  - tests/factory_dashboard/test_app.py
  - tests/factory_dashboard/test_board.py
---

### Goal
The top bar's menu is four slots of a fixed size that never move: Overview, Planning, Board and a sub menu holding the other seven pages, on a phone and on a wide screen.

### Context
Read `.softfield/cards/f194-the-menu-is-a-bit-weird.md` (D1 to D5) and build the Proposed of `.softfield/cards/f194-mockup/menu.html`: its CSS under "proposed" is the picture to copy, on the tokens of `factory_dashboard/static/dashboard.css`.
- `factory_dashboard/templates/base.html`: the `nav.tabs` loop, and the script "Scroll the active tab into view" (f3-30), which goes. The sub menu is a `details` and `summary` inside `nav.tabs`, its pages plain links, so no poll closes it: the live poll swaps only `#planning-tab`, which keeps its id.
- Each page sets `active`. A page whose `active` is in the sub menu lights the fourth slot and names itself there. The floor's `/line` lights nothing, as today.
- f132-08 (it runs first) put the project picker and a `.bay-group` in the strip: D3 puts the `filters` form back in `.bar-top`, as it was, and removes `.bay-group`. Its crumbs ("The whole factory") stay.
- `tests/factory_dashboard/test_app.py` has `test_phone_top_bar_is_compact_and_tabs_scroll`, which asserts the sideways scroll, and the test f132-08 added for the picker: both now assert the opposite. `tests/factory_dashboard/test_board.py` asserts Projects first. Four test files mark `nav.tabs` as `data-layout` overlay for the sideways scroll: remove those marks.

### Done when
- on a 390 px and a 360 px phone the four slots fill the row, each at least 44 px tall, nothing scrolls sideways and no word is cut, with "Planning · 99" and with "Timeline" in the fourth slot
- each slot's left edge is the same on Overview, Planning, Board and Timeline, on a phone and on a wide screen, and when the Planning count goes from 1 to 12
- the sub menu lists Projects, Tickets, Jobs, Runs, Timeline, Agents and Bench in that order, each with its few words from the mock-up, every link keeping the `?project=` as today
- on Jobs the fourth slot is hazard yellow and reads "Jobs"; on Overview it reads "More" and isn't lit; a milestone's page still lights Board
- a tap outside the open sub menu, or Escape, closes it, and it stays open through a live poll
- the project picker is in the bar's top row on every page, and choosing a project reloads the page with it, as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
