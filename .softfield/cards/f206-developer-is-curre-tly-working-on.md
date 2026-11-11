# Milestone F206: The board's developer's view counts tickets a developer has started

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-11. Base: git tag `f206-developer-is-curre-tly-working-on-start`. Report: [`.softfield/reviews/f206-developer-is-curre-tly-working-on.md`](../reviews/f206-developer-is-curre-tly-working-on.md).
> Planted by the owner on 2026-11-02.

## Notes
Developer is curre tly working on f187. On the board developer view it says lead only where it's clearly dev work available

## What we know (2026-11-02, from the code and the metrics)
- `_dev_work` in `factory_dashboard/board.py` counts only tickets whose state is `ready`. The runner marks a ticket `running` when it starts, so a developer ticket drops out of the count the moment a developer takes it.
- F187, Store every time in UTC, has two lead tickets and one developer ticket, f187-02. The local model worked on f187-02 from 22:32 to 23:06, three attempts, and the card read "lead only" throughout.
- The checks then failed a third time (mypy), so f187-02 is now escalated and waits for the lead. The card's "lead only" is close to true today, but it hides that a developer tried.
- `_dev_resolver` has the same gap: a developer ticket that depends on a running developer ticket is said to wait for the lead.
- F146, the board's Developers only view, was checked on an idle queue, so nothing showed this.

## Expected outcome
The developer's view tells the truth while work is under way: a card with a developer on one of its tickets is lit and names that ticket, and a card whose developer ticket was handed on says so instead of "lead only".

## Done when
- A running developer ticket lights its card: "developers: working on f187-02 · then the lead's f187-01".
- A developer ticket that depends on a running developer ticket counts as "after it", not as waiting for the lead.
- An escalated developer ticket reads "developers tried f187-02 · now with the lead"; a blocked one reads "f187-02 is blocked". Both cards stay faded.
- "lead only" appears only on a card with nothing but lead tickets left.

## Decisions
These amend F146's D2 to D4 for tickets that have started.
- **D1 Running counts as the developers' work.** `DevWork` gets `running`, the running developer tickets' ids. A card with any is look `can`, and `_dev_resolver` follows a running developer ticket as it follows a ready one.
- **D2 The Planted head counts it.** A running ticket counts among the tickets developers can work on, at the full median time. Time already spent on it isn't taken off: the head's figure is an estimate.
- **D3 Handed-on tickets stay faded.** `DevWork` gets `with_lead` and `blocked`, the ids of the card's escalated and blocked developer tickets. Developers can't take them, so the look stays `none` and only the words change. On a lit card, such a ticket counts as what's left for `then`, so the card doesn't promise "then Claude's review" too early.
- **D4 The legend's faded entry** reads "faded: nothing for developers to take", since faded is no longer only "lead only".

## Plan (lead, 2026-11-02)
No mock-up: the lit and faded looks stay as F146 drew them, and only the words on a card change.

| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | dev-view-sees-started-tickets | D | 3 | – | D1 to D4 |
