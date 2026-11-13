---
id: f242-01-lane-review-goes-first
milestone: f242-the-review-of-a-fast-lane
agent: lead
difficulty: 4
files:
  - runner/dispatch.py
  - runner/loop.py
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
---

### Goal
The review of a card in the fast lane goes with the lane: queued first among due reviews, run before every other queued job and ticket, and parked only where a lane ticket would be.

### Context
Read "What happened" and D1–D3 in `.softfield/cards/f242-the-review-of-a-fast-lane.md`.
In `runner/dispatch.py`: `GOES_WITH`, `plan` (its `lane_rows`), `pick`.
In `runner/loop.py`: `reserve_cards` and `lane_with_escalated` (the lane as ticket ids), `work_queue` (passes the lane as `first`; its `lane_only` filter), `dry_run_plan`, `_runnable_rows` (holds reviews while a checkpoint or escalation is queued), `_queue_due_review`, `park_review`, `claude_hold` (its `owners` flag uses both reserves), `project_round`.
`runner/milestone.py`'s `card(key, text).reserve` reads a card's fast-lane mark; `due_reviews` lists due reviews in milestone order. A review row's subject is the card's full key; an escalation's is a ticket id, which starts with its card's short key.
`reserve_cards` keeps its meaning (`_uses_reserve` reads it): the lane cards' keys join `first` beside it.

### Done when
- With F191 in the fast lane and its tickets all done, its queued review runs before a planner job, a checkpoint, another card's review and a ready lead or developer ticket, in `work_queue` and in the round's lane pass.
- With two reviews due, the lane card's is queued first, and a checkpoint or escalation of another card doesn't hold it; one of its own card still does.
- With Claude in the owner's share of the 5-hour window, a lane card's review runs and another card's parks, as today; a real limit parks both.
- `softfield run --dry-run` lists the lane card's review in the lane.
- A card out of the lane keeps today's order, queueing and parking (the existing tests pass unchanged).

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
