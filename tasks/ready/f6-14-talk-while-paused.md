---
id: f6-14-talk-while-paused
milestone: f6-planning-room
depends_on: [f5-18-pause]
agent: lead
difficulty: 4
files:
  - runner/dispatch.py
  - runner/loop.py
tests:
  - tests/runner/test_dispatch.py
  - tests/runner/test_loop.py
---

### Goal
While the owner pauses the factory, the planning room still works: their requests (plants, messages, send-backs, approvals) are applied and planner jobs run, so they can pause, talk a change through with the lead on `/planning` and approve it while the line holds. Nothing else starts.

### Context
Read ADR 22 item 5 and its ⚑ amendment (`docs/adr/22-one-visible-queue.md`), `plan` and `pick` in `runner/dispatch.py` (today every line becomes `PAUSED` while paused), and in `runner/loop.py`: `work_queue` (the `paused_by_owner` pick), `_hold_for_the_owner` (it polls `_take_switches`, which applies only the switches, the pause and the resume), and `apply_owner_requests` (every request, at each pick).
- The owner's first dashboard pause (2026-10-07): their "say hi" message to F11 was applied at 08:17 and then waited "paused by you" behind the hold, and a plant made during the hold would not be applied until Resume.
- In `plan`: while paused, a `PLANNER` row keeps its own wait (none, or its `not_before`), every other line gets `PAUSED`.
- In the hold: each poll applies every open request (`apply_owner_requests`, which may commit: the run is git's one writer and nothing else runs while it holds), and the hold ends (back to the pick) as soon as an open planner row exists or the pause is lifted. After the planner job, the pick finds the pause again and holds again, with one "Paused by you" log line per hold, not per poll.
- `--dry-run` shows the planner row as next while paused.
- The hold polls every `SWITCH_POLL_S` (60 s), so the owner's first Resume (2026-10-07) took 45 s and looked broken; they clicked twice. The hold for the owner polls every 5 s instead (its own constant; the 25% wait keeps its 60 s).

### Done when
- a `plan` test: paused, a planner row has no wait and is picked; a ticket, a checkpoint and an escalation still wait "paused by you"
- a loop test: a `plan_message` posted while the run holds is applied and its planner job runs before Resume; a `plant` posted while it holds is applied (its doc committed) before Resume; with no request the run keeps holding
- a resume posted while the run holds is taken within 5 s
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
