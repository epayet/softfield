# Milestone F26: I want to see numbers next to "Coming" and "Your desk" to have a sense of how many there are

> **Status: planned** (2026-10-07, with the owner, in the planning room). **State:** ready · **Priority:** 6 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
(none)

## Outcome
- On `/planning`, the owner sees at a glance how many things are on their way and how many wait for them: "Coming · 2", "Your desk · 5".

## Decisions
- **D1 Same style as Archived:** the headings read `Coming · N` and `Your desk · N`, like `Archived · N` on the same page and `Planning · N` on the tab (`factory_dashboard/templates/planning.html`, `factory_dashboard/templates/base.html`).
- **D2 Your desk counts what the tab counts:** the sum of the four desk groups' items, the same number as the Planning tab (`planning_count` in `factory_dashboard/app.py`), so the two never disagree on a fresh page.
  - **As built (review, 2026-10-10):** the desk has five groups since F31 ("Didn't go through" first), and the number is what still waits for the owner (`waiting_for_you` in `factory_dashboard/planning.py`): a card on its way (dashed, after Archive, Sign off or Remove seed) stays listed and is counted no more, on the heading as on the tab. So the number can be smaller than the cards shown, and a desk holding only cards on their way reads "Your desk" alone.
- **D3 Nothing at zero:** an empty desk keeps "Your desk" with no number ("Nothing waits for you." already says it), as the tab does; Coming is hidden when empty, as today.
- **D4 Totals only:** the four desk groups ("Your answers wanted", "Proposals to review", …) get no count of their own; each lists its items right under it.
- **D5 As fresh as the list:** the numbers are rendered with the lists, so they always match what the page shows. Keeping the page live is F19's question, not this card's.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | desk-counts | D | 2 | – | D1–D4 |

## How to test
Open `/planning` with a plant pending and something on the desk: "Coming · 1" and "Your desk · N", N being the Planning tab's number. Empty the desk: "Your desk" alone.
