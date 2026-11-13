# Milestone F194: The menu: Overview, Planning, Board in fixed places, the rest in a sub menu

> **State:** ready · **Priority:** 6 · **Area:** factory
> Planted by the owner on 2026-11-02.

## Notes
The menu is a bit weird being horizontal scroll. The places of the items keep moving when going from page to page. There are 3 critical pages (maybe 4 with projects, but k suspect I won't at it _that_ often): overview, planning, board. Everything else could be accessible through a sub menu instead

## Why it happens (from the code, 2026-11-02)
- `factory_dashboard/templates/base.html` draws ten tabs. Under 640 px `nav.tabs` scrolls sideways (`dashboard.css`, f3-30), and a script on every page load scrolls the current tab to the middle of the strip. So the items are somewhere else on each page: the shift is built in, not a bug.
- On a wide screen the tabs sit at their words' width, so the Planning count going from 9 to 12 pushes every tab after it.

## Outcome
Three pages one tap away, in places that never change, on a phone and on a wide screen; everything else one tap further, in a sub menu that says what each page is.

## Done when
- f194-01 merged.
- To test, on the phone: open Overview, then Planning, then Board. The four slots stay exactly where they are and nothing scrolls sideways. Tap More, then Timeline: the fourth slot turns yellow and reads "Timeline"; the other three haven't moved. Tap outside an open sub menu and it closes.
- Then on a wide screen, the same.

## Decisions
- **D1. Four slots of a fixed size.** Overview, Planning, Board, More, in that order. On a phone they fill the row in fixed proportions; on a wide screen they have fixed widths. Nothing scrolls, and neither the current page nor the Planning count moves them. The script that centres the current tab goes.
- **D2. The sub menu.** A `details` inside `nav.tabs`, a plate hung from the fourth slot, listing in this order: Projects, Tickets, Jobs, Runs, Timeline, Agents, Bench, each with a few words on what it is. It closes on a tap outside or Escape. This replaces "Projects first" in the strip (ADR 30's tab order): Projects is first in the sub menu, and the owner expects to use it rarely.
- **D3. The project picker stays in the bar's top row,** on every page and width. This reverses F132's D7 (the picker in the tab strip, in front of Planning, Board and Tickets): with Tickets in the sub menu that group no longer exists, and a phone's row has no room for a picker beside four slots. f132-08 runs first and keeps its crumbs; this card's ticket undoes only where it put the picker.
- **D4. The fourth slot says where you are.** On a sub-menu page it is hazard yellow and shows that page's name in place of "More", at the same size.
- **D5. Plain links stay.** Every page in the sub menu is an ordinary link carrying `?project=`, and `#planning-tab` keeps its id for the live count.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | four-slot-menu | D | 4 | f132-08 | D1 to D5 |

It waits for f132-08 (F132, One view of the whole factory: the top bar, the Overview, Jobs and the floor) because both change the same lines of `base.html`; waiting pulls that ticket forward if this card is dragged ahead of F132.

The mock-up: `.softfield/cards/f194-mockup/menu.html` (Today and Proposed, real values of 2026-11-02).
