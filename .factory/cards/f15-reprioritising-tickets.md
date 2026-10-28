# Milestone F15: Reprioritising tickets

> **State:** ready · **Priority:** 8 · **Area:** factory
> Planted by the owner on 2026-10-07.

## Notes
I believe this feature will be availaible as part of the board view. That view is not available yet, when will it be?

### From F18: Arrow to reprioririse queue (merged by the owner on 2026-10-13)
Once we have a proper board to prioritise, I don't think this will be useful? You can only do so on the top 3 items in the queue. And it gets tricky if a task depends on another. 
When will the initial board view be done? I forgot if we planned it

## Edit the board (planned with the owner, 2026-10-13)
The board (`/board`, F5) is read-only. The owner wants to reorder and act from it, and dislikes the ↑ ↓ arrows of Next in line: "do all the changes and once I'm happy I send go and the re-order gets picked up later". This card now covers F18 (the arrows) and F54 (an arrow press shows nothing): once the board orders cards, the arrows go and F54's plan is not needed.

**The picture:** [`f15-mockup/board-edit.html`](f15-mockup/board-edit.html), on the board's real cards of 2026-10-13, with a Today / Proposed switch (also <https://claude.ai/artifact/Uw5Ygr2fz8TfUy1XCjrK2Z>). The owner tried it on a phone and approved the plan and the mock-up on 2026-10-13 ("other than that it looks great"), after three rounds.

## Expected outcome
- On the board the owner drags cards into the order they want, sees what moved and from where, and sends the new order once; the runner follows it from its next pick.
- The board opens on the field: six plots that grow from seed to harvest, with nothing scrolling sideways on a phone.
- A card's menu leads to its conversation, its sign-off and setting it aside. The ↑ ↓ arrows are gone from the other pages.

## Done when
- On a phone, open the board, tap the Planted plot, drag a card to the top: it says "moved · was #N · not sent yet". Drag it back: the mark goes. Move two cards, press "Send new order": both read "on its way … at the runner's next pick". After the runner's next pick the marks go, the order stays, and Next in line follows it.
- Next in line and the Milestones page have no arrows.

## Decisions
- **D1 Drag by a grip, inside a stage.** Each card has a grip to drag it by and a place (#1, #2…) in place of its P number; the page scrolls near its edges. "Top / Up / Down / Bottom" in the card's ⋯ menu does the same without dragging. A card can't be dragged to another stage: the stage comes from the work (F5 D4).
- **D2 On a phone, one stage at a time,** picked from the field: six plots in growth order, three to a row, each with its plant (taller stage by stage, a crate at harvest) and its count. Nothing scrolls sideways (the owner, 2026-10-13, on the first mock-up's row of chips).
- **D3 One send.** A moved card says where it was ("moved · was #7"), so it can be put back (the owner, 2026-10-13). A card put back where it was is not moved, nor are the cards it passed (the owner, 2026-10-13): what is out of place is worked out from the order, not from what was touched. Moves stay on the page, dashed orange "moved · not sent yet", with a bar at the bottom: "3 cards moved · Cancel · Send new order". Sending makes one request, `reorder`, whose value is the open cards and bug tickets in the order shown.
- **D4 On its way at once.** The board draws the sent order from the open request, dashed orange "at the runner's next pick", on any device, until the runner has applied it; sending again replaces it.
- **D5 The runner applies it at its next pick,** in one commit: it sets the cards' `Priority:` (and the bug tickets' `priority:`) so the order holds, changing as few files as it can. The job running is not interrupted. A ticket's own `priority:` still wins over its card's. A lead ticket (`runner/requests.py` is protected); no new ADR, as ADR 19 item 4 foresaw moves from the board as ADR 18 requests.
- **D6 A card says what it waits for** (the owner, 2026-10-13: "'wait for fxx' sounds like a good mvp approach"). A planted or growing card none of whose ready tickets can start says "waits for F22", naming the other cards. It never refuses a move: the runner skips a waiting ticket whatever its place.
- **D7 Actions on a card** (⋯): open its conversation, set aside (F73), open the card. A ripe card has no ⋯: its own link already reads "Read the review and sign off ›" and opens its review (F110). Planting stays on the planning desk (the lead's recommendation, in the mock-up the owner approved): the desk is what waits for the owner, in order of importance; the board is every card and their order. Both read one rule for what is ripe and what is being planned (F110).
- **D8 The arrows go** from Next in line and the Milestones page once D5 is built.
- **D9 The drag code is our own:** the mock-up's pointer code, in `factory_dashboard/static/board.js`. It worked on the owner's phone, and a vendored library would be one more protected file for forty lines.
- **D10 One order for every open card.** Priorities are one line, not one per stage: the page sends the whole open order, and a move inside a stage puts the card just before the card it was dropped above. A card shows its place in its stage; the runner sees the whole line.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | reorder-request | L | 6 | – | D3, D5, D10: the `reorder` request and what the runner does with it |
| 02 | board-shows-the-order | L | 5 | 01, f110-03 | D1, D4: a place on each card, a sent order on its way with "was #N" |
| 03 | the-field | L | 5 | 02 | D2: the six plots, one stage at a time on a phone |
| 04 | drag-and-send | L | 7 | 03 | D1, D3, D9: drag by the grip, the move menu, the bar, one send |
| 05 | replan | L | 3 | 04 | 06 and 07 checked against what 01 to 04 built |
| 06 | card-actions | D | 4 | 05, f73-02 | D7: conversation, set aside, the card |
| 07 | arrows-go | L | 3 | 05 | D8: the arrows leave Next in line and the Milestones page (it removes a file) |
| 08 | card-says-what-it-waits-for | D | 3 | 02 | D6: "waits for F22" on a card whose tickets can't start |

Who builds: 01 is protected; 02 to 04 are a new module, a new script and a phone layout, the kind the local model has not passed (F6, F8, F3's `factory.js`); 06 is a template per card and a few lines of `board.js` beside the send it copies.

## Replan
**2026-10-20, f15-05**, after f15-01 to f15-04 were merged. 06 and 07 checked against main.

What changed:
- **06, the menu is one dialog, filled by the script.** The ticket had the ⋯ menu in each card's markup; f15-04 built one `#order-sheet` that `board.js` fills on a press, and a ⋯ only on the four stages the owner orders. 06 now renders each card's actions in a `<template>` inside its slot (so the page tests can read them), and `board.js` copies it into the sheet. `board.js` and `dashboard.css` join its files; difficulty 3 → 4. Its set-aside example is `#archive-button` in `thread.html`, which is on main (f73-02's `#set-aside-button` is not yet); the dependency on f73-02 stays so the words match F73's "Set aside".
- **06 and D7, no sign-off in the menu.** A ripe card has no ⋯, and its link already ends in `#review` and says "Read the review and sign off ›" (f110). Giving ripe cards a ⋯ for the same link would add a menu with no moves; D7 now says so.
- **06, set aside shows on its way.** The card learns of an open `archive` request, so after a reload the button still says "on its way" (the owner, 2026-10-07: show what was asked at once). The ⋯ label becomes the mock-up's "Actions for F27", and the test that allows only a `reorder` from the board allows `archive` too.
- **07, what only served the arrows.** `up`/`down` in `line.py` and `milestones.py` and `queries.moves` serve only the arrows; `_with_moves` also sets each milestone row's priority, which must stay. 07 names them, the `.move*` CSS and the four tests to replace, and adds `test_board.py`.
- **07, the board's foot.** The page never said the Milestones list keeps the arrows; only a Jinja comment in `board.html` and a test's docstring do. 07 now names those.
- **07, the Queue panel's terminal command.** Above Next in line it says "Drain it with <code>…</code>", against the owner's rule of 2026-10-13 (no terminal commands on the dashboard's pages). 07 edits `queue.html` anyway, so it drops that line too.

Seen and not changed:
- A ripe card has no ⋯ (above). Suggested fix if the owner wants one for symmetry: give ripe cards 06's ⋯ with "Read the review and sign off" alone, a follow-up ticket after 06; no action until asked.

## Folded in
- **F18, Arrow to reprioritise queue:** answered by D8; merged here by the owner on 2026-10-13 (its notes are above).
- **F54, the reprioritise up down arrows do nothing:** not needed once the arrows go. Its draft plan and mock-up are still on its thread: press Reject there.
