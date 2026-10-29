---
id: f65-04-drop-a-round
milestone: f65-what-happens-if-i-comment-on
agent: lead
difficulty: 4
depends_on: [f65-01-review-rounds]
files:
  - runner/requests.py
  - factory_dashboard/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
The owner can drop a review round: one Set aside request naming a card sets aside every one of its tickets not yet started, so the card goes back to To sign off with its earlier review.

### Context
Read `.factory/cards/f65-what-happens-if-i-comment-on.md` (D6), then the `SET_ASIDE` branch of the request handler in `runner/requests.py` (it calls `loop.set_aside` for one blocked ticket today), `set_aside` in `runner/loop.py`, `_approve_plan` in `runner/requests.py`, and `factory_dashboard/requests.py` (what it accepts as a `set_aside` subject).
- A `set_aside` whose subject is a card's short key (`f38`) and whose value is `round` moves that card's tickets in `.factory/tasks/ready/` and blocked to later/, in one commit, leaving the one in flight (`state.in_flight`) to finish. Its answer names the tickets: "set aside f38-02-updated-note: F38 is back for your sign-off".
- Requests run in the order they were made, so a drop sent before the runner took the Approve still works: the approval queues the tickets, then the drop sets them aside.
- A `set_aside` naming a ticket works as today.

### Done when
- a round drop on a card with two ready tickets sets both aside in one commit and says so
- with one of them in flight, that one is left and the answer says it will finish
- an approve then a drop, in one pick, leaves the card's new tickets in later/
- a round drop on a card with no ready ticket changes nothing and says so
- a `set_aside` naming a blocked ticket works as before
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
