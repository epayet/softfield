# Milestone F197: Plant and ask the lead comes first and yellow; Plant turns plain

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-11-02.

## Notes
Reverse plant and 'plant and ask the lead '. Plant without asking should be secondary option not yellow

## Outcome
Wherever the two planting buttons sit together, the yellow one, placed first, asks the lead; the plain one beside it only plants.

## Done when
- The Plant box on the Planning page shows "Plant and ask the lead" first in yellow, then "Plant" as the plain button, and the line beside them says them in that order.
- A review's idea plate shows them the same way.
- Each button still does what it did.

## How to test
1. Open Planning: Plant and ask the lead comes first, in yellow; Plant comes second, plain.
2. Plant a note with each: Plant and ask the lead queues the lead's reply on its thread; Plant leaves a seed on your desk that waits for you.
3. Open the thread of a reviewed card with an unplanted idea: its plate shows the same two buttons in the same order.

## Decisions
- **D1: the same two buttons, swapped** (mock-up `.softfield/cards/f197-mockup/plant-buttons.html`): `#plant-ask` takes `btn go` and goes first, `#plant-only` takes `btn plain`. Ids, words and what each sends stay. This replaces the colours f81-03 gave them. Only the buttons change: the hint keeps its words, in the new order.
- **D2: the idea plate follows** (f197-02): F164's plate is about to be built with the old order, and the weekly report's ideas (f59-04) reuse it. It changes once f164-03 is on main, in F197, as F164's tickets aren't this card's to edit.

## Tickets
- f197-01-plant-box-asks-first (developer)
- f197-02-idea-plate-asks-first (developer, after f164-03-idea-plates-with-plant)
