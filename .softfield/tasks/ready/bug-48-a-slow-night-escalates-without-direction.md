---
id: bug-48-a-slow-night-escalates-without-direction
milestone: bugs
difficulty: 4
depends_on: []
agent: lead
area: factory
finding: f15-reprioritising-tickets-F3
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
When the local model is slow for a whole run, a ticket that stops twice with no edit goes straight to the lead, without a direction and a third attempt that would stop the same way.

### Context
Read `def needs_direction`, `def _queue_direction` and the attempt loop that calls them (the `elif` before `_queue_direction` in `runner/loop.py`), `STOP_NO_EDIT` and `def stop_reason` in `runner/local_model.py`, and the tests of `needs_direction` and of a queued direction in `tests/runner/test_loop.py`. `runner/**` is protected: write the tests first, each failing for the right reason.
- Five tickets in two nights (f73-01, f73-02, f103-01 on 2026-10-29 09:14; f185-01 and f15-06 on 2026-10-29 22:21) stopped "no edit after 20 min" on both attempts, got a direction, and stopped a third time the same way; each was then escalated and the lead did it in one session. Each direction and third attempt cost Claude's window and 20+ minutes of the run for nothing. `runner/instructions/lead.md` (Known range, f73-01's line) has asked for this check since 2026-10-29; the direction job sees one ticket and can't count the others.
- The rule: before queueing a direction, if every attempt of this ticket so far ended on `STOP_NO_EDIT`, and this run already has at least two other tickets whose attempts all ended on `STOP_NO_EDIT`, don't queue the direction or run the last attempt: escalate the ticket at once, with a reason that says so ("the local model made no edit on N tickets this run").
- Count from what the run already records (the attempt's stop reason is saved as the job's note by `_finish_attempt`), not from a new state file.

### Done when
- a ticket with two no-edit stops, in a run where two other tickets already ended on no-edit stops, is escalated at once: no direction job is queued, no third attempt runs, and its reason names the run's no-edit count
- with only one other such ticket in the run, the direction is queued as today
- a ticket whose earlier attempts failed a gate, or timed out, still gets its direction whatever the run's count
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
