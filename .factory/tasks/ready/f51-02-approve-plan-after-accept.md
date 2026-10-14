---
id: f51-02-approve-plan-after-accept
milestone: f51-when-a-plan-depends-on-an
difficulty: 4
depends_on: []
agent: lead
files:
  - runner/requests.py
  - tests/runner/test_requests.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
Once the owner has pressed Accept ADR, they can approve the card's plan at once; the runner refuses a plan whose drafted ADR is still Proposed after its turn.

### Context
Read `_adr_waits` and `proposal_review` in `factory_dashboard/planning.py`, the Approve plan button in `factory_dashboard/templates/proposal.html`, and `_approve_plan`, `_owners_marks`, `_ticket_problems`, `_proposed` and `_accept_adr` in `runner/requests.py`.
- The owner (2026-10-08): a plan waiting on an ADR they already accepted "shouldn't count as something on my desk".
- D2 (`.factory/cards/f51-when-a-plan-depends-on-an.md`): `_adr_waits` counts an open `accept_adr` request (`done IS NULL`, subject the card, value the ADR's number) as accepted. The page then enables Approve plan and shows, in the muted style of today's line: "ADR N's acceptance is on its way: the runner applies it first." Requests run oldest first (`metrics.open_requests`), so the accept is applied before the approval.
- D3: after the squash merge in `_approve_plan`, refuse with main as it was ("not approved: relies on ADR N, still Proposed: accept it first") when an ADR the branch adds or changes is Proposed on the merged tree. Today `_owners_marks` lets a branch's new Proposed ADR through, so a failed accept would let its plan merge.
- Test-first: the runner's refusal, and the accept-then-approve order in one pick, in `tests/runner/test_requests.py`.

### Done when
- an open `accept_adr` for the card's ADR: the plan's page has Approve plan enabled and the line above; without one, it is disabled as today
- one pick with `accept_adr` then `approve_plan` for the same card: the ADR is Accepted, then the plan merges and its tickets queue
- `approve_plan` alone while the branch's ADR is Proposed: refused, main unchanged, the reason names the ADR
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
