# Milestone F103: The Planning tab's number counts only what you have to answer, not seeds

> **State:** ready · **Priority:** 10 · **Area:** factory
> Planted by the owner on 2026-10-10.

## Notes
The number of things in planning number in tab should not count seeds not planted. The number should be for thing i have to do. Essentially just proposals

### From F161: I don't want seeds not planted yet to count as a… (merged by the lead on 2026-10-20)
I don't want seeds not planted yet to count as a notification next to the planning link. I want it to stay lean with things I actually have to answer

## What happens today
On 2026-10-20 the tab reads "Planning · 67": 3 answers wanted, 3 proposals and 61 seeds. The number is `len(waiting_for_you(desk(...)))` (`factory_dashboard/app.py`), and `waiting_for_you` in `factory_dashboard/planning.py` counts every desk group's items not on their way, the "Seeds, not asked about yet" group included. The same list makes "Your desk · N" on `/planning`, the Overview's "N things wait for you on your desk", the Projects page's count and the Previous / Next between desk pages (F35).

## Expected outcome
The number next to Planning counts only what the owner has to act on: answers wanted, proposals to review, what didn't go through, blocked tickets and cards to sign off. Seeds stay listed on the desk, with their own group number (F26, Numbers next to Coming and Your desk), and count nowhere else.

## Decisions
- **D1 Seeds wait on no one** (the lead, 2026-10-20): `waiting_for_you` leaves out the `seeds` group. One change, so every reader follows: the Planning tab, "Your desk · N", the Overview's Needs you, the Projects page and the Previous / Next trail, which no longer steps through seeds. The desk still lists the Seeds group, last, with its own number from f26-02.
- **D2 Not proposals only:** the owner's note said "essentially just proposals"; an answer the lead wants, a note that didn't go through, a blocked ticket and a card to sign off also wait for the owner's action, so they stay counted.
- **D3 No mock-up:** only a number changes; no element is added, moved or restyled.

## Tickets
- f103-01-seeds-not-counted (developer): D1, after f26-02-group-counts, whose "groups add up to the desk's number" now leaves Seeds out.
