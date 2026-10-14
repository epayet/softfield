# Milestone F22: move archive button on planning desk at the bottom rather than the top

> **State:** ready · **Priority:** 1 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
- The owner (2026-10-07): move the archive button on a planning thread to the bottom rather than the top.

## Expected outcome
On a card's thread (`/planning/<card>`), the top shows only the card's name; the Archive (or Unarchive) button and, on a seed, "Remove seed" sit at the bottom of the page, under the reply box, where you are once you've read the thread to the end.

## Done when
- The Archive row comes after the conversation and the reply box, on a phone and a desktop.
- On a phone, the sticky Send box still sticks while you read, and the Archive row shows once you scroll to the end.
- "Remove seed" moves with it, so the top holds no button that ends a card.
- Everything else about archiving is unchanged: on its way it shows at once with a dashed orange edge, the button goes, and a reply opens the thread again.

## How to test
Open a thread with a few messages on the phone: the top is the card's name only; scroll down past Send to find Archive; tap it and see "Archiving at the runner's next pick".

## Decisions
- D1. The row goes after `#conversation`, not inside it: the Send box is sticky at the bottom of `#conversation` on a phone, so a row inside would be hidden under it or stick with it.
- D2. "Remove seed" moves too: both end a card, and both belong where you've finished reading.
- D3. F30 (newest answer first) may reorder the thread later; if it does, the Archive row stays at the very bottom of the page, and F30 updates this ticket's position test.

## Tickets
- `f22-01-archive-at-the-bottom`
