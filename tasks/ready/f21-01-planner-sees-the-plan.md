---
id: f21-01-planner-sees-the-plan
milestone: f21-lead-briefs
difficulty: 5
depends_on: []
agent: lead
files:
  - runner/planner.py
  - runner/loop.py
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_loop.py
---

### Goal
A planner job's prompt says where the work stands, from the runner's own order, so the lead answers "when will X be done?" and "where does this fit?" from facts.

### Context
Read `docs/milestones/f21-lead-briefs.md` (D1 is what the block holds and its size limit), `runner/loop.py` (`dry_run_plan`: the same inputs; `run_planner`: where the prompt is built), `runner/tasks.py` (`run_order`, `pick_next`), `runner/planner.py` (`prompt`, and `history` as the pattern for a block the runner writes into it).
- The block is built by the runner, never by Claude reading files.
- **Read-only: building the block changes nothing in `tasks/`, the run state or the database.**

### Done when
- with a ticket in flight, three ready tickets over two cards with different priorities and one waiting on a dependency, the prompt lists the one in flight, then the three in pick order, each with its milestone and who does it, and "waits for <id>" on the waiting one
- every card shows with its state and priority
- the median duration of the last 20 merged tickets shows, in minutes; with none merged, the line says so
- past 25 ready tickets, the rest are a count, not lines
- a planner job's prompt carries the block (a `run_planner` test, as `test_a_thread_with_replies_but_no_session_gives_the_lead_its_history` in `tests/runner/test_loop.py` does)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
