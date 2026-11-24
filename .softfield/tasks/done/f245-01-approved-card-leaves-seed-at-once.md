---
id: f245-01-approved-card-leaves-seed-at-once
milestone: f245-i-accpedfed-a-plan-as-go
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_order.py
---

### Goal
A card whose plan the owner approves shows as Planted on the board at once, not as a Seed until the runner's next round.

### Context
Read "What happened" and D1 in `.softfield/cards/f245-i-accpedfed-a-plan-as-go.md`, then `apply_owner_requests` and `sync_cards` in `runner/loop.py`, `_approve_plan` in `runner/requests.py` (it writes the card `ready` on main but not the `milestones` row) and `_milestone_stage` in `factory_dashboard/board.py` (an `idea` card with no open thread is a Seed). Follow `test_each_projects_first_apply_of_requests_moves_it_and_the_table_follows` in `tests/runner/test_order.py` for a session that applies requests. `runner/**` is protected: tests first.

### Done when
- after `apply_owner_requests` applies an `approve_plan` request for an idea card with a ticket drafted on its `plan/<card>` branch, the card's `milestones.state` row reads `ready`, with no other session step in between
- a request that changes nothing (no request waiting) does not read the cards again
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
