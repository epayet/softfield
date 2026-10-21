---
id: f106-05-replan-brings-back-blocked
milestone: f106-where-do-blocked-tickets-go-for
difficulty: 6
depends_on: [f106-04-lead-looks-at-a-block]
agent: lead
files:
  - runner/requests.py
  - runner/planner.py
  - docs/agents/lead.md
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_planner.py
---

### Goal
A replan may bring its card's blocked tickets back: reworked into `.factory/tasks/ready/`, or set aside in `.factory/tasks/later/` (ADR 29 item 3).

### Context
Read `.factory/adr/29-the-lead-looks-at-a-blocked-ticket.md` (item 3; it must be Accepted), then `_approve_plan`, `_outside`, `_ticket_problems` and `_owners_marks` in `runner/requests.py`, and what the planner's prompt in `runner/planner.py` says a replan may touch (`drafts` gives the job's edit globs). `runner/**` is protected: write the tests first.
- On the plan branch, a replan may remove `.factory/tasks/blocked/<card>-*.md` when the same ticket appears in `.factory/tasks/ready/` or `.factory/tasks/later/` on that branch. Approving it applies that with the rest, and resolves the ticket's open `blocked` owner item.
- A ticket brought back to ready must pass pre-flight, as any ticket a replan changes.
- Refused, main unchanged, with a plain reason: another card's blocked ticket; a blocked ticket removed and put nowhere; one edited but left in `.factory/tasks/blocked/`.
- A headless job can't move a file: the planner writes the reworked ticket at its new path, and the runner removes the blocked copy when it commits the drafts or applies the approval. Decide which, and say so in the prompt.
- The planner's prompt and the "Planning room" section of `docs/agents/lead.md` say a replan can do this.

### Done when
- approving a replan that reworks its card's blocked ticket: the ticket is in `.factory/tasks/ready/` with the new text and its old runner footers, gone from `.factory/tasks/blocked/`, its `blocked` item resolved, and the owner's pause lifted as for any replan
- approving one that sets it aside: the ticket is in `.factory/tasks/later/`, gone from `.factory/tasks/blocked/`, its item resolved
- each refusal above leaves main and the database as they were and names the ticket
- a reworked ticket that fails pre-flight refuses the approval with its problems
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
