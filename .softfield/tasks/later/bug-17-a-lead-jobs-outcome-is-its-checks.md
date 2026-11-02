---
id: bug-17-a-lead-jobs-outcome-is-its-checks
milestone: bugs
difficulty: 3
depends_on: []
agent: lead
area: factory
priority: 42
finding: f153-i-wonder-if-sonnet-would-be-F4
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
A lead-ticket job whose `check-all` failed is recorded as failed, so the first-time pass rate can be read from the jobs.

### Context
Read `def _settle_lead_task` and `def _settle_or_step_up` in `runner/loop.py`. `runner/**` is protected: tests first.
- A lead-ticket job's `jobs.outcome` is its session's, not its `check-all`'s: a Sonnet attempt that failed `check-all` reads "passed". ADR 32 item 6's first-time pass rate needs the check's result.
- Finish such a job "failed" with the note "check-all failed"; a job whose check passed stays "passed".

### Done when
- a Sonnet lead attempt whose session ends well and whose `check-all` fails: its job reads failed, note "check-all failed", and the Opus step-up still runs
- one whose `check-all` passes reads passed
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
