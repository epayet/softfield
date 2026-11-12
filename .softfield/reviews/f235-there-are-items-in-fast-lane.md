# Review: F235, the fast lane goes before planner replies in the multi-project run

## Sign-off sheet

### 1. What changed
When Claude's limit frees up, a fast-lane ticket now goes first in `softfield run`, ahead of queued planner replies, directions, checkpoints and escalations, across every project, as Next in line already showed. Two steps:
- every round now starts with each project's fast lane (its tickets, and the directions and escalations about them);
- the queued-jobs pass runs **one** job and then the round starts again, so a long backlog of old directions (each leading to a last attempt on Qwen and maybe an escalation) can no longer hold the lane for hours, as it did on 10 November from 02:29 past 08:00.

Pausing still gets the owner's planning replies first: while any project is paused, the lane pass is skipped.

The card had no mock-up and no after pictures: nothing on screen changes.

### 2. How to test it yourself
1. Put a card in the fast lane whose first ticket can run, and leave a planner reply or two queued (write on a card's thread).
2. Wait for Claude's limit to free up (or start `softfield run` with Claude free).
3. On the dashboard, the lane's ticket should be the next thing running, before the planner replies. The replies come after it.
4. Pause the factory and write on a thread: the reply should still be answered while paused.

### 3. Left for later
Nothing.

### 4. Decisions waiting for you
None: this brings the runner in line with ADR 35 (Accepted).

### 5. How the work went
- 2026-11-10, terminal sessions led by Claude: f235-01 built by the lead in 663b878e (with f191-01, the same fault), then a follow-up e0f16893 once the night run showed old directions still holding the lane. No runner jobs, no local tokens.
- Lessons: the first fix put the lane first only at the start of a round; one queued-jobs pass could still run for hours, because a direction queues a last attempt and an escalation behind it. "One job, then ask the lane again" is the rule that holds. The lead should check a fix against the incident's whole chain of jobs, not only the first one.

### 6. What next
- **Product:** product work stays on hold, as the owner asked.
- **Factory:** the next lane delay would only be caught by the owner noticing. A small check worth a ticket later: on the dashboard, flag when a lane ticket that can run has waited behind other jobs for more than one job's turn.

### 7. What clogged the factory line
For this milestone itself, nothing: the lead built it directly in terminal sessions, with no runner jobs. The fault it fixes was the clog: on 9 November about 20 minutes and $28 of planner replies ran before f139-03 at the 16:00 reset, and on 10 November eight old directions and their escalations ran from 02:29 past 08:00 before the lane got a turn. That is now unclogged by the two changes above.

## What was built
- `project_round` (`runner/loop.py`): a lane pass first, each project in the owner's order, `turn(s, lane_only=True, once=True)`; skipped while any project is paused.
- `work_queue`: `lane_only` keeps only the lane's ticket and the directions and escalations about lane tickets; without `take_tickets` it now returns after one queued job.
- Tests: the round's order with a lane job, without one, and while paused; the lane pass runs the lane ticket and not the planner reply, and runs nothing without a lane ticket; the queued pass runs one job, then returns. The helper `_turns` got the new keyword; no existing assertion changed.

## Findings and resolutions
- **F1 (nit, fixed by the lead in this review):** `project_round`'s docstring still said a round runs "every project's queued jobs" after e0f16893 made it one. Reworded.

The tests are close to the incident and fail without the change (the one-job test raises if a second job starts). No missing edge case worth a ticket: a parked review continues the loop as before, and a job that parks for Claude's limit still counts as a pick, so the round restarts at once with the lane.

No French in this milestone.

## Set aside
Nothing.

## Workflow observations
- The two lane fixes (F191-01 and F235-01) were the same fault, found twice by the owner on the same evening; merging the cards early would have saved a ticket.
- This review's range held other milestones' work; reviewing only the listed commits worked well.

<!-- runner report -->
<!-- /runner report -->
