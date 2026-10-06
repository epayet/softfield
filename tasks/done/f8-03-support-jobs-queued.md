---
id: f8-03-support-jobs-queued
milestone: f8-one-queue
depends_on: [f8-02-dispatch]
agent: lead
difficulty: 7
files:
  - runner/loop.py
  - runner/milestone.py
  - runner/state.py
tests:
  - tests/runner/test_loop.py
---

### Goal
The runner queues its support jobs before running them, and its loop runs whatever `pick` returns.

### Context
Read `docs/adr/22-one-visible-queue.md`, D1–D3 in `docs/milestones/f8-one-queue.md`, `runner/dispatch.py` (f8-02), and in `runner/loop.py` `note_merge`, `give_direction`, `handle_escalation`, `_park`, `_resume_support` and `work_queue`; `_due_review` (also in `runner/loop.py`) and the review loop in `runner/milestone.py`; `runner/state.py` (`parked`). Test-first.
- Each trigger keeps its rule and only queues a row with its reason: a checkpoint "after <a> and <b> merged", a review "<KEY>'s tickets are all done", a direction "<id> failed: <gates>", an escalation "<id>: <reason>".
- Parking (D3) sets the row's `not_before`; an old `var/runs/state.json` with `parked` entries is turned into rows once, at start.
- A ticket waits behind its own queued direction or escalation, as today.

### Done when
- tests: each trigger leaves a queued row with its reason, and the row is finished with its job's id when the job ends
- a parked checkpoint survives a restart as a row and runs after its reset
- the existing loop tests still pass (the order of what runs is unchanged)
- `uv run runner check-all --task f8-03-support-jobs-queued` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
