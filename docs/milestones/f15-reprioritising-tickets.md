# Milestone F15: Reprioritising tickets

> **State:** planning · **Priority:** 2 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
I believe this feature will be availaible as part of the board view. That view is not available yet, when will it be?

## Edit the board (planned with the owner, 2026-10-13)
The board (`/board`, F5) is read-only. The owner wants to reorder and act from it, and dislikes the ↑ ↓ arrows of Next in line: "do all the changes and once I'm happy I send go and the re-order gets picked up later". This card now covers F18 (the arrows) and F54 (an arrow press shows nothing): once the board orders cards, the arrows go and F54's plan is not needed.

**The picture:** [`f15-mockup/board-edit.html`](f15-mockup/board-edit.html), on the board's real cards of 2026-10-13, with a Today / Proposed switch (also <https://claude.ai/artifact/Uw5Ygr2fz8TfUy1XCjrK2Z>). Not agreed yet: the tickets are written once the owner has tried it on a phone.

## Decisions to settle on the mock-up
- **D1 Drag by a grip, inside a stage.** Each card has a grip to drag it by and a place (#1, #2…) in place of its P number; the page scrolls near its edges. "Top / Up / Down / Bottom" in the card's ⋯ menu does the same without dragging. A card can't be dragged to another stage: the stage comes from the work (F5 D4).
- **D2 On a phone, one stage at a time,** picked from a row of chips with each stage's count, so a drag never crosses 35 planted cards and five other lists.
- **D3 One send.** Moves stay on the page, dashed orange "moved · not sent yet", with a bar at the bottom: "3 cards moved · Cancel · Send new order". Sending makes one request, `reorder`, whose value is the open cards and bug tickets in the order shown.
- **D4 On its way at once.** The board draws the sent order from the open request, dashed orange "at the runner's next pick", on any device, until the runner has applied it; sending again replaces it.
- **D5 The runner applies it at its next pick,** in one commit: it sets the cards' `Priority:` (and the bug tickets' `priority:`) so the order holds, changing as few files as it can. The job running is not interrupted. A ticket's own `priority:` still wins over its card's. A lead ticket (`runner/requests.py` is protected); no new ADR, as ADR 19 item 4 foresaw moves from the board as ADR 18 requests.
- **D6 Dependencies show.** A card moved up whose tickets wait for another card's says "waits for …"; not drawn in the mock-up yet.
- **D7 Actions on a card** (⋯): open its conversation, set aside (F73), read the review and sign off (F110), open the card. Plant an idea from the Seed stage.
- **D8 The arrows go** from Next in line and the Milestones page once D5 is built.
- **D9 The drag code:** a vendored SortableJS file in `factory_dashboard/static/vendor/` or the mock-up's own 40 lines of pointer code; decided after the phone trial.
