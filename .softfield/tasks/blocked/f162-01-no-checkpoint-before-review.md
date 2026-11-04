---
id: f162-01-no-checkpoint-before-review
milestone: f162-doing-a-checkpoint-just-before-a
agent: lead
difficulty: 3
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A developer merge that its milestone's review is about to read no longer counts toward a checkpoint, so a milestone's last merges go straight to its review.

### Context
Read `.softfield/adr/38-no-checkpoint-the-review-will-read.md` (items 1–4), then in `runner/loop.py`: `note_merge`, `lead_work_ready`, `checkpoint`, `_queue_due_review`; and `due_reviews`, `_reviewed` and `RESTART` in `runner/milestone.py` (it imports `runner.loop`, so import from it inside the function, as `_queue_due_review` does). The existing checkpoint tests in `tests/runner/test_loop.py` (search `note_merge`) are the example to follow.
- `unchecked` and `recheck` entries are `"<ticket> <sha>"`; a ticket's milestone is in its `.softfield/tasks/done/` frontmatter.
- "Covered" (item 1): the ticket's milestone is in `due_reviews(repo, state)`, or its `state.review_stop` is `RESTART`. Compare by `short_key`.
- One helper drops covered entries from both lists and saves the state; `note_merge` calls it before its count, `checkpoint` at its start. When `checkpoint` is left with nothing, it finishes its row with no Claude job and logs item 4's line.

### Done when
- a developer merge that completes its milestone, with one unchecked merge of the same milestone before it, queues no checkpoint, and `unchecked` is empty after it
- the same with one unchecked merge of another milestone still building: no checkpoint, and that merge stays in `unchecked`
- a fix ticket merged while its milestone's review stopped at `restart` queues no checkpoint
- a checkpoint queued before the milestone's last merge finishes without a Claude job, and the review is queued at the next pick
- two merges of a milestone still building queue a checkpoint as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: blocked
reason: the lead ticket changed nothing
```
