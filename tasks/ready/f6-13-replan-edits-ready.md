---
id: f6-13-replan-edits-ready
milestone: f6-planning-room
depends_on: [f6-12-merge-duplicates, f5-18-pause]
agent: lead
difficulty: 6
files:
  - runner/planner.py
  - runner/requests.py
  - runner/prompts.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
---

### Goal
The owner can redirect a milestone that is running, from the planning room. A `replan` proposal can change, add or set aside that milestone's ready tickets. Approving it applies the changes while the line is paused, then resumes.

### Context
Read F6's D2 and its "Later" note in `docs/milestones/f6-planning-room.md` (a `replan` can't edit ready tickets yet), `is_draft` and `parse_reply` in `runner/planner.py`, the `approve_plan` handling in `runner/requests.py`, the planner prompts in `runner/prompts.py`, and the pause f5-18 built (its request kinds and the `State` field it added).
- The owner (2026-10-06): "my goal is to steer and plan the work from the planning UI, so I need less of this stop-the-factory-and-chat-in-the-terminal".
- **On the branch:** a `replan` proposal's plan branch may also carry edits to its own milestone's `tasks/ready/` tickets: changed, added, or moved to `tasks/later/`. Never another milestone's, never a running ticket (the one in the runner's state file's `in_flight`), never `tasks/done/`. `is_draft` grows a check that takes the card.
- **While talking:** the owner can pause the line (f5-18) so nothing starts from a ticket being changed. The planner's reply says when it advises a pause.
- **On approval:** pre-flight runs on every changed ticket first. Any problem refuses the approval, naming it, and nothing is applied. Then the branch merges as for a plan, and a pause the owner set is lifted.
- Update D2 ("As built") and the "Later" note.

### Done when
- a `replan` branch editing its milestone's ready ticket is approved and the ticket on main changes; the same edit to another milestone's ticket, or to the running ticket, is refused with its reason
- a changed ticket that fails pre-flight refuses the approval, and main is unchanged
- approval lifts the owner's pause; without a pause, approval still applies
- the planner prompt says what a `replan` may change and when to suggest a pause
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
