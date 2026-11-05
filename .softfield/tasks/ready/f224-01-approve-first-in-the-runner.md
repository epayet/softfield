---
id: f224-01-approve-first-in-the-runner
milestone: f224-i-want-to-be-able-to-2
agent: lead
difficulty: 3
depends_on: [f222-01-approved-goes-last]
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
An `approve_plan` request with the value `first` approves the plan as usual, puts the card first in the queue's order and in the fast lane, in the approval's one commit.

### Context
Read `.softfield/cards/f224-i-want-to-be-able-to-2.md` (D1–D4) and `.softfield/adr/35-a-marked-card-goes-first.md`.
- `runner/requests.py`: `_apply` calls `_approve_plan` and passes no value today; `_approve_plan` writes the approval's commit; `_card_marked` writes the header's mark; `_card_reserve` calls `_free_parked` once marked.
- f222-01, which this waits for, has `_approve_plan` put a card last in the queue's order list and tell the database (ADR 45 item 3). Going first uses the same write, with the card at the head.

### Done when
- `first` on a plan with a ticket: the card ends up ready, first in the list ahead of every open card and bug, and marked `**Fast lane:** yes`; every other card and bug keeps its order, and it is all one commit
- a card already in the fast lane stays marked once, and still moves first
- `first` on a replan moves a card already in line to the head and marks it; the replan's other effects, the pause lifted included, are as without it
- the marked card's parked tickets go at the next pick, as with the lever (`_free_parked`)
- a plan with no ticket in ready after the approval is approved as if plain: no mark, no move, and the result says nothing goes first
- a merge-only approval with `first` applies the merge and moves nothing
- no value behaves exactly as before; any other value is refused before anything changes, with its words in the result
- a refused approval leaves the list and the doc as they were
- the result ends "F224 goes first on the board, in the fast lane", with the card's own name, and still starts with `approved`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
