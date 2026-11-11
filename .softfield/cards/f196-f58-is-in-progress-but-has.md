# Milestone F196: A planted card with no tickets, and an old ADR that lost its Accept button

> **State:** ready · **Priority:** 15 · **Area:** factory
> Planted by the owner on 2026-11-02.

## Notes
F58 is in progress but has no tickets, can't do anything about it

## What happens today (read in the code, 2026-11-02)
- **F58 shows as planted with nothing to run.** On 2026-10-08 the owner approved F58's merge of F57. That approval also merged F58's plan branch, which held only ADR 27 and the card's doc. `_approve_plan` (`runner/requests.py`) sets a card ready whatever it queued, so F58 became ready with no tickets. It is the only such card today.
- **F58's page has lost its Accept button.** The proposal's stored path is still `docs/adr/27-…`, from before the ADRs moved. `_ADR_NUMBER` (`factory_dashboard/planning.py`) only reads `.softfield/adr/…`, so `proposal.html` draws no Accept ADR. Send back and Reject are all that's left, and Reject works today.
- **Remove seed is hidden too:** `_header` (`factory_dashboard/thread.py`) offers it only on an idea, and the runner refuses it on anything else.
- **A rejected ADR that's on main stays Proposed:** `_reject` deletes the branch and the card, and leaves the ADR's status line as it was.
- **The hole is narrower now:** since F51, a drafted ADR must be accepted before its plan can be approved, and since F127, accepting an ADR on a card with no tickets asks the lead for the plan. A plan holding only a mock-up or a doc still makes a card ready with no tickets.

## Expected outcome
A card is planted only when it has tickets. A card with none stays a seed the owner can write on or remove. An old ADR proposal offers Accept when its file is on main, and rejecting an ADR says so in the ADR.

## Decisions
- **D1 Ready means it has tickets:** `_approve_plan` sets a card ready only when a ticket of the card exists, in any folder of `.softfield/tasks/`, once the plan is merged. Otherwise the card keeps its state.
- **D2 Old paths count only when the file is there:** a stored `docs/adr/<name>.md` reads as `.softfield/adr/<name>.md`, and its number counts only if main has a file of exactly that name. F27's old proposal names `docs/adr/27-planning-beside-the-line.md`, which is gone, while main's ADR 27 is F58's. Reading the number alone would give F27's page an Accept that accepts F58's ADR, because `_accept_adr` goes by number when there's no plan branch. `.softfield/adr/…` paths read as they do today: their drafts live on the plan branch.
- **D3 Reject marks the ADR:** when the owner rejects a set holding an ADR whose exact file is on main and still Proposed, `_reject` sets it Rejected through `owner.decide_adr`. The same exact-name check as D2 keeps F27's reject away from F58's ADR.

## Tickets
- `f196-01-old-adr-paths`: developer, D2.
- `f196-02-ready-needs-a-ticket`: lead, D1, and puts back any card that's ready with no ticket.
- `f196-03-reject-marks-the-adr`: lead, D3.

No mock-up: nothing new is drawn. The Accept button is the one the page already has, and a card with no tickets sits in a column that already exists.

## How to test
1. Open ADR 27 on F58, when i ask the lead a question, if it's still there: Accept ADR is back.
2. Open F27, when i pause the factory: its old ADR offers Send back and Reject, no Accept.
3. On the board, no card under Planted is without a ticket count.
