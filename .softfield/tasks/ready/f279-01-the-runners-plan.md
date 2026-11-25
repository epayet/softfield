---
id: f279-01-the-runners-plan
milestone: f279-i-would-like-to-be-able
agent: lead
difficulty: 6
depends_on: []
files:
  - runner/loop.py
  - runner/planner_job.py
  - runner/waits.py
  - runner/dispatch.py
  - runner/metrics.py
  - runner/cli.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_dispatch.py
  - tests/runner/test_metrics.py
---

### Goal
The runner works out the whole factory's plan (every project's jobs and tickets in the order it will take them, each with why, and one sentence on what drives the order) at each pick, stores it, and `softfield run --dry-run` prints that same plan.

### Context
Read `.softfield/cards/f279-i-would-like-to-be-able.md` (D1–D4) and the Proposed side of `.softfield/cards/f279-mockup/queue.html` for what the sentence and the facts read like.
- Today: `def dry_run_plan` in `runner/loop.py` prints one project's list from `dispatch.plan` and `choose_ticket`; `_run_projects` in `runner/cli.py` loops it per project. `def project_round` is the factory's order (D3). `def work_stands` in `runner/planner_job.py` reads the same inputs for the planner.
- Split `dry_run_plan` into data and printing: `factory_plan(configs, at)` returns `dispatch.FactoryPlan` (D2); the dry run prints it as one list, each line with its project, `->` on the pick, each ticket's pre-flight problems under it.
- The sentence and facts (D4) come from what `choose_ticket` reads (`_pick_windows` in `runner/waits.py`, the lane, `state.owner_pause`, `_held_by_red_main`, `allowance.pace_line`); the developers' runway uses the median of `ticket_minutes` (`runner/planner_job.py`).
- Storing: a `queue_plan` table in `runner/metrics.py` (one row, replaced), `store_queue_plan(conn, plan)` and `latest_queue_plan(conn) -> dict | None`. `run_projects` stores it before each job starts and on a round that ran nothing, at most once a minute.
- Take in `.softfield/tasks/later/bug-21-dry-run-plans-with-the-runs-windows.md`: a job held by Claude's limits says what the run would do with it (park, or a stand-in), not "waits".
- `runner/**` is protected: tests first.

### Done when
- with two projects, a queued checkpoint in the second and a developer ticket that can go in the first, the plan lists the checkpoint first, then the ticket, each with its project and group
- over pace, the sentence reads "Over pace: developers first, the lead when nothing else can" with the week's reading and the developers' runway as facts; paused by the owner, the sentence says so first; at Claude's limit, it says until when
- a ticket with a pre-flight problem carries it in `preflight`
- `softfield run --dry-run` prints one list for every project, the pick marked, and writes nothing
- a run stores the plan before a job starts; `latest_queue_plan` returns it with `at` and `picked`; a round that runs nothing stores it at most once a minute
- with Claude at its limit and a checkpoint due, its line says it would park or go to a stand-in (bug-21)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
