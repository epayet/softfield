---
id: f196-03-reject-marks-the-adr
milestone: f196-f58-is-in-progress-but-has
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/requests.py
tests:
  - tests/runner/test_requests.py
---

### Goal
When the owner rejects a proposal set holding an ADR already on main, that ADR's status says Rejected, so it doesn't sit as Proposed for ever.

### Context
Read `.softfield/cards/f196-f58-is-in-progress-but-has.md`: "What happens today" and D3.
- `runner/requests.py`: `_reject` deletes the card's plan branch and removes a card with nothing built. It doesn't touch `.softfield/adr/`.
- `runner/owner.py`: `decide_adr` sets the status, in one commit, and resolves the owner items about that ADR. Pass `path=` so it can't pick another file of that number.
- `runner/planner.py`: `is_proposed` reads the status line.
- A stored path may be `docs/adr/<name>.md` or `.softfield/adr/<name>.md`. Compare the file name, not the number: F27's old proposal has the same number as F58's ADR on main, but it's a different ADR.

### Done when
- rejecting a set whose ADR's exact file name is on main and Proposed sets that file to `Rejected (by the owner, <date>)`
- a set whose ADR isn't on main (a draft that goes with its branch), an ADR of the same number under another name, and an ADR already Accepted are left as they are
- a reject that only closes a merge or a seed changes no ADR
- if F58's card has left `.softfield/cards/` when this ticket runs, the owner has already rejected its ADR, so this ticket sets the file named the-lead-acts-when-asked in the ADR folder to Rejected, dated the day of that commit, and says so in its commit. If the card is still there, it leaves that ADR alone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
