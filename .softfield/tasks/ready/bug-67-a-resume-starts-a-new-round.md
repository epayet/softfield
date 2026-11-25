---
id: bug-67-a-resume-starts-a-new-round
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
When the owner resumes a held run, the runner goes back to the round, so the fast lane is asked first, as ADR 35 item 2 says. It doesn't carry on with the next queued job of the project whose turn held.

### Context
- On 2026-11-25 the owner resumed at about 08:38 and the fast lane had five runnable tickets (f290-09 first). The runner ran a direction for f124-04 (not a lane card) and then the direction's last attempt, about 40 minutes of the local model, before any lane ticket.
- Why: `project_round` in `runner/loop.py` computes `held` once, at the start of the round. While held it skips the lane and gives each project a turn with `take_tickets=False`. In that turn, `work_queue` finds no job and calls `_hold_for_the_owner(s)` (around line 825). When the hold returns True the loop `continue`s, so after a resume the same turn picks its project's next queued job (a direction, checkpoint or escalation), and a direction's last attempt runs within that job.
- `_hold_for_the_owner` also ends when a planner job can go (`_planning_goes`). That case should keep running the planner job in the same turn. Only a hold that ended in a resume (`s.state.owner_pause is None`) goes back to the round. ADR 54 (bug-66) will make a resume the hold's only end: write this so it still holds then.
- A single project's run (`run_session`, no round) has no lane order to restore. Check what `work_queue` returning there means, and keep `test_a_resume_while_the_run_holds_is_taken_at_the_first_poll` (`tests/runner/test_loop.py`) passing unchanged.

### Done when
- with two projects, the owner's pause held and a lane ticket ready in the second project while the first has a queued direction for a ticket outside the lane: after the resume, the lane ticket is the next thing that runs, then the direction
- a hold that ends because a planner job can go still runs that planner job in the same turn (an existing planner-while-paused test still passes unchanged)
- `test_a_resume_while_the_run_holds_is_taken_at_the_first_poll` passes unchanged
- the listed `tests:` pass, and the new one fails without the change
- all gates pass (see `docs/workflow.md`)
