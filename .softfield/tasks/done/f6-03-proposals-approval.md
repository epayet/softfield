---
id: f6-03-proposals-approval
milestone: f6-planning-room
depends_on: [f6-02-planner-prompt]
agent: lead
difficulty: 7
files:
  - runner/planner.py
  - runner/requests.py
  - runner/owner.py
  - runner/metrics.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
---

### Goal
Approving a card's proposals from the dashboard merges its drafts into main, accepts its ADR and queues its tickets, and nothing else ever does.

### Context
Read `docs/adr/20-planning-room.md` items 6–7, D4 in `docs/milestones/f6-planning-room.md`, `runner/requests.py` (F5), `runner/owner.py` (`decide_adr`), `runner/tasks.py` (`preflight`) and `runner/planner.py`. Test-first.
- **New request kinds** (D1): `accept_adr` (the card, the ADR number), `approve_plan` (the card) and `send_back` (comments on a proposal's key points, which become a `plan_message`).
- **`approve_plan`:**
  - merges `plan/<card>` into main, refusing if the branch touches anything but `docs/` and `tasks/`;
  - pre-flights every ticket it adds, and on problems refuses with them as the result, so the planner fixes them on the next message;
  - moves the card's tickets from `tasks/later/` to `tasks/ready/`, and sets the card's state to ready.
- **`accept_adr`** runs `decide_adr` after merging the ADR draft. A plan whose tickets rely on a Proposed ADR can't be approved before it.

### Done when
- `approve_plan` on a clean branch merges it, queues its tickets and sets the card ready; a branch touching `runner/` is refused, and main is unchanged
- a ticket with a bare path refuses the approval with the problem named
- `accept_adr` merges and accepts; `approve_plan` before it is refused when a ticket needs the ADR
- `uv run runner check-all --task f6-03-proposals-approval` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
