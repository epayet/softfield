---
id: f191-01-lane-before-every-project-s-queue
milestone: f191-why-is-the-lead-reviewing-something
agent: lead
difficulty: 5
depends_on: [f191-05-fix-ticket-holds-only-its-review]
files:
  - runner/loop.py
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
Under `softfield run`, the fast lane goes before every project's queued jobs: a lane ticket that can run is taken before a due review, a planner job, a checkpoint or a direction, in any project.

### Context
Read "What happened" and D1 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md`, then ADR 35 items 2 and 5 in `.softfield/adr/35-a-marked-card-goes-first.md`.
In `runner/loop.py`: `project_round` (its first pass calls `turn(s, take_tickets=False)`, so `work_queue` never asks `_next_task` and the lane has no ticket in it), `run_projects`' `turn`, `work_queue`, `_next_task` (it calls `choose_ticket`, which the runner and the dry run share since F219) and `reserve_cards`. A lane ticket goes past the week's pace line (F219 D5), so a lane lead ticket held only by a real limit is the one that gets passed over.
Tests to follow: `test_every_projects_queued_jobs_go_before_any_ticket` and `_turns` in `tests/runner/test_loop.py` for the round; `test_the_fast_lane_goes_before_a_due_parked_ticket_and_the_board` for a lane in `work_queue`.
On 2026-10-29 at 21:06 F21's review ran two rounds this way while fast-lane tickets of F85 and F175 waited. The owner kept ADR 35 as it is: the planner's jobs wait for the lane too.

### Done when
- A round runs every project's fast lane first (its lane tickets, and a queued direction or escalation of one), then every project's queued jobs, then one ticket from the first project that has one, as today.
- With a due review queued and a lane lead ticket ready in the same project, the round runs the lane ticket; the review runs once the lane has nothing it can run.
- A lane ticket in the second project goes before a planner job in the first.
- A lane ticket that can't run (a real Claude limit, a dependency not done) is passed over, and the queued jobs go on.
- While the owner pauses, no lane ticket runs and the planner's jobs still do.
- With no card in the fast lane, a round runs what it does today, in the same order (the `project_round` tests keep their assertions; `_turns` may learn the new pass).
