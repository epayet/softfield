---
id: f6-24-plan-shows-tickets
milestone: f6-planning-room
depends_on:
- f6-29-fix-coming-misses-unpicked-message
- f6-30-fix-sent-message-tests-thin
agent: lead
difficulty: 5
files:
  - runner/planner.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/runner/test_planner.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
Before approving a `plan` or a `replan`, the owner sees on its review page what approving changes: each ticket the plan branch adds, changes or sets aside, and each doc it drafts, with the text of each, so a replan of a running milestone is never approved on its key points alone.

### Context
Read F6's D2 ("As built (f6-13)") and D4 in `docs/milestones/f6-planning-room.md`; in `runner/planner.py` `draft`, `is_draft` and `is_ready_ticket`; in `runner/requests.py` `_drafts` and `_ready_changes` (what approval reads from the branch); and `proposal_review` and `mockup_file` in `factory_dashboard/planning.py` with `factory_dashboard/templates/proposal.html`.
- Today `planner.draft` reads only `docs/` and `tasks/later/` (`is_draft(path)` with no card), and the review page shows only the key points and a mock-up. F6's "Later" listed showing a replan's edited ready ticket; the f6-19 replan made it a ticket, since approving a replan is the step of the steering loop that changes running work.
- Add to `runner/planner.py` one function the dashboard calls, reading git only (planner jobs check the branch out): the plan branch's changes since it left main (`main...plan/<card>`), each with its path and one of "added", "changed", "set aside" (a ready ticket removed and moved to `tasks/later/`) or "removed"; an empty list with no branch or for the general thread. `draft` also reads the card's own ready tickets (`is_draft(path, card)`), still refusing every other path as today.
- On the review page of a `plan` or `replan`: a "What approving changes" section listing each path with its word, its text (escaped, folded in a `<details>`) read through `draft`, none for a removed file. "What happens next" says, for a `replan`, that approving applies the ticket changes at once, even while paused, and resumes the line.
- Security: `draft` stays the dashboard's only way to read the branch; isolation tests show it refuses another card's ready ticket, `tasks/done/`, code, `..` and a path outside the repo, as before.

### Done when
- a replan branch that changes the ticket f7-01-a, adds f7-03-c and moves f7-02-b from `tasks/ready/` to `tasks/later/` lists the three with "changed", "added" and "set aside" (the last once, under its `tasks/ready/` path), each with its text from the branch; main's copy of f7-01-a is not shown
- `draft` reads the ready ticket f7-01-a on `plan/f7`, and refuses another card's ready ticket (f8-01-x) there
- a card with no plan branch, and the general thread, show no such section
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
