---
id: bug-65-a-pause-holds-planning
milestone: bugs
difficulty: 5
depends_on: []
agent: lead
area: factory
files:
  - runner/dispatch.py
  - runner/loop.py
  - runner/requests.py
  - runner/prompts.py
  - runner/instructions/lead.md
  - .softfield/adr/22-one-visible-queue.md
  - .softfield/cards/f6-planning-room.md
tests:
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
  - tests/runner/test_requests.py
---

### Goal
While the owner pauses the factory, nothing runs and nothing is written to the repo: no planner or setup job, and no request applied except the resume. At the resume, the requests that waited are applied in the order they came, and the runner resumes only onto a main folder that is on main and clean.

### Context
Build `.softfield/adr/54-pause-holds-planning.md` (Accepted 2026-11-25), items 1 to 7. Read it first.
- `dispatch.PLANNING` (`runner/dispatch.py`, "never held by their pause") and the `paused` branch of `dispatch.plan` let planner and setup rows through a pause. The module docstring's pause bullet says the same: rewrite it to say ADR 54.
- `_hold_for_the_owner` and `_planning_goes` in `runner/loop.py` end the hold whenever a planner job can go. With ADR 54 the hold ends only at the resume. Its poll calls `apply_owner_requests`, which applies every request (`apply_requests` in `runner/requests.py`); during the hold, only a resume may be applied (with `check_backup` still running). Plants, approvals and the board's order commit on main (`commit_all` in `runner/requests.py`), which is why they must wait.
- ADR 54 item 6: at a resume, if the main folder (`s.git`) is not on `main` or `git status --porcelain` shows anything, the run stays held and says "the folder has changes that aren't committed: commit or undo them, then resume" (or that it is off main, naming the branch). It goes on at the next poll once the folder is clean, with no second resume.
- The paused status line is "Paused by you since …: only planning goes until you resume" (around line 1364 of `runner/loop.py`). It becomes "nothing runs until you resume; what you send waits for it". A planner row's wait while paused reads "waits for your resume".
- `prompts.PLANNER` (`runner/prompts.py`, around "suggest the owner pause the factory from the dashboard first … approving the `replan` lifts their pause") must stop suggesting a pause. Remove the part of `approve_plan` in `runner/requests.py` that lifts a pause, and its `resumed` suffix.
- Docs (ADR 54 item 7): add one line under ADR 22 item 5's ⚑ "Except planning" and under F6 D1 "While paused" and D2 "As built (f6-13)", each pointing to ADR 54. In `runner/instructions/lead.md`'s "The steering loop" bullet, say that a replan runs after the resume. Leave lead.md's "(or paused on main)" line as it is.
- Tests that check the old behaviour (planner rows passing a pause, approval lifting a pause, the hold ending for a planner job) change with it. Only those, and say which in the commit message.

### Done when
- while paused, `dispatch.plan` gives every row, planner and setup ones included, the wait "paused by you" (the planner's own words: "waits for your resume"), and the pick returns nothing
- during the hold, a queued plant, message and approval stay unapplied in the database and the repo gets no commit. After a resume they are applied in the order they were made, before the first pick
- a resume while the folder has a change that isn't committed keeps the run held with the message above. Committing it lets the run go at the next poll with no second resume. The same holds for a folder on another branch
- approving a `replan` while paused (once applied at the resume) leaves no `resumed` suffix and doesn't change the pause
- the planner prompt no longer mentions pausing before a `replan`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
