---
id: f6-22-hold-polls-fast
milestone: f6-planning-room
depends_on: []
agent: lead
difficulty: 2
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
While the owner pauses the factory, what they ask from the dashboard (a resume, a message, an approval, a priority) is taken within 5 s, not up to a minute later.

### Context
Read `_hold_for_the_owner` and `_planning_goes` in `runner/loop.py`, and `SWITCH_POLL_S` (60 s, the wait for the owner's 25%), and in `tests/runner/test_loop.py` the tests that use `_holds_then_resumes` (they assert `slept == [loop.SWITCH_POLL_S, …]`).
- f6-14's Done when asked for "a resume posted while the run holds is taken within 5 s"; the merge kept `time.sleep(SWITCH_POLL_S)` in the hold, and no test checks it. Found by the f6-19 replan.
- The owner's first dashboard Resume (2026-10-07) took 45 s and looked broken; they clicked twice. Each step of the steering loop while paused (send a message, approve a replan, move a priority, resume) waits for this poll.
- Give the hold its own constant (5 s); the 25% wait keeps `SWITCH_POLL_S`. The hold still logs one "Paused by you" line per hold, not per poll.

### Done when
- the hold sleeps 5 s between polls; the 25% wait still sleeps `SWITCH_POLL_S`
- a resume posted while the run holds is taken at the first poll, 5 s after the hold starts
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
