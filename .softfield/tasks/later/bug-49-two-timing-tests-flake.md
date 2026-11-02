---
id: bug-49-two-timing-tests-flake
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
finding: f90-editing-seeds-that-i-ve-planted-F2
tests_only: true
files:
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
Two timing tests in `tests/runner/test_loop.py` stop failing now and then on unrelated work.

### Context
From the old backlog file, in the review's words:

Two timing tests in `tests/runner/test_loop.py` fail now and then on unrelated work: `test_the_heartbeat_advances_during_a_usage_limit_pause` (three beats in a 0.5 s real-time window) and `test_with_the_week_switch_off_a_lead_ticket_at_the_reserve_parks_for_the_owner` (`fake_clock[0] == THURSDAY` exactly; it moved 1 ms). They failed Sonnet's right f90-01 and paid an Opus step-up ($0.32). Fix: assert the clock moved less than a minute ("it didn't sleep till Monday"), and wait for the beats with a deadline instead of a fixed window. Next: a bug ticket in `.softfield/tasks/later/` at the next backlog pass (protected `runner/` tests: the lead's).

### Done when
- the two tests pass reliably under a loaded machine and still fail without the behaviour they check
- the listed `tests:` pass
- all gates pass (see `docs/workflow.md`)
