---
id: f235-01-lane-before-every-projects-jobs
milestone: f235-there-are-items-in-fast-lane
agent: lead
difficulty: 5
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
`softfield run` honours ADR 35 item 2 ("the fast lane goes before everything"): a fast-lane ticket that can run goes before every project's queued jobs (planner replies, escalations, directions, checkpoints, reviews), as Next in line already shows.

### Context
Read `.softfield/adr/35-a-marked-card-goes-first.md` (items 2, 4, 5), `project_round`, `run_projects`, `work_queue` and `reserve_cards` in `runner/loop.py`, `plan` in `runner/dispatch.py`, and the `project_round` tests near `_turns` in `tests/runner/test_loop.py`.
- **The fault, measured on 2026-11-09:** Claude's 5-hour window reset at 16:00. `project_round` first calls each project's `turn(s, take_tickets=False)`, so `work_queue` offers `dispatch.pick` no ticket at all and the lane never reaches it: seven queued planner replies ran 16:00–16:19 (jobs 1911–1917, about $28), then F139's fast-lane ticket `f139-03-rebuild-clashing-plan-branches` started at 16:19 and parked for the limit two minutes later. At the 21:00 reset two more planner replies ran ahead of it again. `dispatch.plan` orders the lane correctly; the single-project `runner run` path is right; only the multi-project round skips it.
- **The fix (F235 D1):** `project_round` gets a first pass, before the queued-jobs pass: each project in the owner's order, while no project is paused, is asked for its fast lane only (a new `work_queue` keyword, e.g. `lane_only=True`, through `turn`). In that pass `work_queue` offers only the lane: a ready ticket of a lane card or one they wait for (`reserve_cards`), and the queued direction or escalation about one of them; nothing else runs, and it returns after one job, as `once` does. A project with no runnable lane job runs nothing in that pass. Then the round goes on as today.
- A pause holds the lane too (ADR 35 item 5): while any project is paused, skip the lane pass, so planning replies still go.
- Update `project_round`'s docstring, and the one-line order in `work_queue`'s, to say the lane goes first across projects.

### Done when
- a round where one project has a runnable fast-lane ticket and another a queued planner job runs the lane ticket first, and the planner job in the next round
- a round with no lane job anywhere calls each project's queued jobs, then one ticket, exactly as the existing `project_round` tests expect (update `_turns` for the new keyword, not the assertions)
- while any project is paused, no lane pass runs and planning replies still go
- in the lane pass, `work_queue` with a queued planner row and a runnable lane ticket runs the ticket, and with only a queued planner row runs nothing
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
