# Milestone F26: I want to see numbers next to "Coming" and "Your desk" to have a sense of how many there are

> **Status: planned** (2026-10-07, with the owner, in the planning room). **State:** ready · **Priority:** 1 · **Area:** factory
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
- **D4 Each group has its number too** (owner, 2026-10-13: "I want numbers next to Proposals to review and your answers wanted, and other similar sections too"; it replaces "totals only", built by f26-01): every desk group's heading reads `<name> · N`: "Didn't go through", "Your answers wanted", "Proposals to review", "Finished, to talk through" ("To sign off" after F63) and "Seeds, not asked about yet".
  - N counts what the desk's number counts (D2, as built): the group's items still waiting for the owner, not the ones on their way. So the groups' numbers add up to "Your desk · N".
  - A group holding only cards on their way shows its name alone, as the desk does (D3).
- **D5 As fresh as the list:** the numbers are rendered with the lists, so they always match what the page shows. Keeping the page live is F19's question, not this card's.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | desk-counts | D | 2 | – | D1–D3, and D4 as first agreed (totals only); done |
| 02 | group-counts | D | 2 | f63-01-desk-order | D4 |

## How to test
Open `/planning` with a plant pending and something on the desk: "Coming · 1" and "Your desk · N", N being the Planning tab's number. Empty the desk: "Your desk" alone. Each group's heading carries its own number ("Proposals to review · 2"), and the groups' numbers add up to the desk's; archive a thread from its page and, until the runner's next pick, its card stays dashed while its group's number and the desk's each drop by one.
