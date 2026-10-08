---
id: f49-01-auto-merge
milestone: f49-don-t-ask-me-to-merge
difficulty: 7
depends_on: [f31-01-settle-and-reject]
agent: lead
files:
  - runner/loop.py
  - runner/requests.py
  - runner/planner.py
  - runner/prompts.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_requests.py
  - tests/runner/test_prompts.py
---

### Goal
The runner applies a planner reply's `merge` proposals itself, right after the job, without the owner's approval.

### Context
Read `docs/milestones/f49-don-t-ask-me-to-merge.md` D1 and D2, and F6's D2 and D4 in `docs/milestones/f6-planning-room.md`. In `runner/loop.py`: `run_planner`. In `runner/requests.py`: `_merges`, `_merge`, `_merged` and `_approve_plan` (its merge-only path). In `runner/planner.py`: `merge_cards`, `merge_words`, and the proposal state f31-01 adds there.
- After `parse_reply`, before the reply is stored: for each `merge`, run `_merge` and `_merged` (make them public, one shared helper), commit `F44 merged into F41 by the lead` on main with the lead as author, and mark the proposal `applied` in the stored proposals, so its state is approved and the desk shows no button.
- Refused when the duplicate has a ticket in `tasks/` (as today) or a plan branch with drafts: the proposal stays open, as today, and the reply's note says why.
- The planner job runs on a plan branch: switch back to main for the commit (as `_commit_drafts` does) and leave the branch as it was.
- `prompts.PLANNER` and `prompts.PLANNER_GENERAL`: a merge is applied at once by the runner, the lead picks the kept card by D2, and nothing about approval is said.
- **Protected work: test-first.**

### Done when
- a reply on F49 with a `merge` of F48 (an idea) into F46 removes F48's doc, adds its notes to F46's, and commits once on main as the lead; F48's thread points to F46's
- the stored merge proposal is `approved`; no owner item asks for it
- a merge whose duplicate has a ticket in `tasks/`, or a `plan/` branch with drafts, changes nothing and stays open, with a note on the reply
- a reply with a merge and a `plan` keeps the plan's drafts on its branch, and the plan stays open
- the planner prompts no longer say a merge waits for the owner
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
note: built by the lead in a terminal session (owner, 2026-10-08), without f31-01: an applied merge is stored with `applied: true`
```
