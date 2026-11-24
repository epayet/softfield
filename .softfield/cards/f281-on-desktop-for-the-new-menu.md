# Milestone F281: Every page in one row on a wide screen, no More

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-20.

## Notes
on desktop for the new menu, there's more space so the fold of more is not needed, could just have all the buttons pages in one row

## Why it happens (from the code, 2026-11-23)
- F194 (The menu: Overview, Planning, Board in fixed places, the rest in a sub menu) drew four slots at every width: `factory_dashboard/static/dashboard.css` lines 161-191 give them 120, 150, 92 and 130 px on a wide screen, about 490 px of a 1250 px row. `base.html` lines 200-213 put the other seven pages in a `details.more` at every width, so on a laptop they take two clicks with room to spare.

## Expected outcome
From 640 px up, Overview, Planning and Board come first, then as many of the other seven pages as the window fits, and More holds the rest; when all seven fit, More goes. Each window width has one layout, so going from page to page never moves a slot. The phone keeps F194's four slots and More.

Picture: `.softfield/cards/f281-mockup/one-row.html` (Today against Proposed with a width slider, real values of 2026-11-23).

**Done when:** f281-01 is merged. To test, on the desktop at full width: the row reads Overview, Planning, Board, a striped seam, then Projects, Tickets, Jobs, Runs, Timeline, Agents, Bench, with no More. Open Timeline: its own slot turns yellow and no slot has moved. Hover Jobs: "every job an agent ran, newest first". Narrow the window step by step: pages leave the row from Bench backwards and More comes back listing only the pages that left; at about 900 px it holds Timeline, Agents and Bench. On the phone: as today.

## Decisions
- **D1. The three, a seam, then what fits.** Overview, Planning, Board at F194's widths (120, 150, 92 px), a 14 px seam drawn with the hazard stripe (ornament, `--stripe`), then the seven sub-menu pages in F194 D2's order at fixed widths of 110, 100, 76, 76, 110, 96 and 86 px, in 12.5 px type, then More (130 px) when any page is left over. Fixed widths, so neither the page nor the Planning count moves a slot (F194 D1 holds).
- **D2. Steps in CSS, not a script.** Because every slot has a fixed width, the window width at which each page fits is known in advance: `@media (min-width: …)` steps at 650 (Projects), 750 (Tickets), 830 (Jobs), 900 (Runs), 1010 (Timeline) and 1070 px (all seven, More hidden; with More gone there is room for Agents and Bench together). No script measures the bar, so nothing jumps after the page loads or when the live poll rewrites `#planning-tab`. Under 640 px the phone's bar is F194's, unchanged.
- **D3. One list, two drawings.** `base.html` draws the seven both as plain links in the row and in the sub menu, from the same `more_pages` list, each with an index (1 to 7); a step's CSS shows the row links up to its index and the sub-menu links past it. The row's links carry `?project=` and their few words as `title`. The current page lights its own slot in the row; when it is in More, the fourth-slot naming of F194 D4 lights More and names it.
- **D4. The steps follow the widths.** A step is the three (362 px) + seam (14) + the pages shown + More (130) + the bar's 32 px padding, rounded up. If a width in D1 changes, its steps change with it; the ticket's tests check each step's row neither overflows nor leaves a gap wider than the next page.

## Before and after
- `/`
- `/timeline`

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | one-row-on-wide | D | 3 | | D1 to D4 |
