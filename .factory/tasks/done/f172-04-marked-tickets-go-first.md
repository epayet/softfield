---
id: f172-04-marked-tickets-go-first
milestone: f172-i-d-like-to-be-able
agent: lead
difficulty: 5
depends_on: [f172-07-fast-lane-in-the-card, f173-02-waited-for-goes-first]
files:
  - runner/dispatch.py
  - runner/loop.py
tests:
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
---

### Goal
The fast lane goes before everything: the ready tickets of a card in the fast lane, and the tickets they wait for, are the runner's next jobs before any planner job, escalation, direction, checkpoint, review, parked ticket whose reset has passed, or other ticket; a direction or escalation of one of them goes with it.

### Context
Read ADR 35 in `.factory/adr/35-a-marked-card-goes-first.md` (it must be Accepted) and D7 in `.factory/cards/f172-i-d-like-to-be-able.md`. Then `plan`, `pick`, `_rank` and `_ticket_rank` in `runner/dispatch.py`; in `runner/loop.py`: `reserve_cards` (the lane's ticket ids), `_next_task`, the pick in the session loop (where `_dispatch_ticket` and `dispatch.pick` are called), and the dry run's list that calls `dispatch.plan` with every ready ticket. f173-02 (merged before this) changed `_next_task` and `pick_next` so a waited-for ticket runs in its waiter's place: build on it.
- `first` is a parameter of `plan` and `pick`, so `dispatch.py` stays pure; empty, the order is exactly today's. `factory_dashboard/overview.py` calls `dispatch.plan` without it and must keep working.
- A queued direction's or escalation's `subject` names its ticket; check how `open_rows` writes them before matching.
- `_next_task` takes a lane ticket first, before the parked ones whose reset has passed, in `pick_next`'s order. A lane ticket that can't run (Claude limited, a dependency stuck) is passed over and the next job is picked, so the line never stands idle for the lane.
- The owner's pause stays as it is: every ticket waits, planner jobs go (`plan`'s `paused`).

### Done when
- with a planner job, a checkpoint and a review queued, and a fast-lane card's ticket ready, `dispatch.pick` returns the ticket
- a queued direction for a lane ticket goes before a queued planner job; a direction for another ticket keeps today's place
- with `first` empty, `plan` returns the same lines as before for the same input
- `_next_task` returns a lane ticket, or a ticket it waits for, over a parked ticket whose reset has passed and over a ticket higher on the board
- with Claude limited, a developer ticket is picked while the lane's lead ticket waits
- while the owner pauses, a lane ticket waits and a planner job is picked
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
