---
id: f89-01-probe-before-planner
milestone: f89-does-allowance-refresh-at-the-beginning
agent: lead
difficulty: 2
depends_on: []
files:
  - runner/loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
Before any Claude job, a planner reply included, the runner takes a fresh reading of Claude's windows whenever the stored one is over 10 minutes old, not only once per runner session.

### Context
Read `.factory/cards/f89-does-allowance-refresh-at-the-beginning.md` (Notes, D2), then `fresh_reading`, `lead_work_ready`, `Session.probed` and `STALE_READING` in `runner/loop.py`, and the probe tests near `test_no_probe_when_the_reading_is_under_ten_minutes_old` in `tests/runner/test_loop.py`.
- Today `fresh_reading` returns early when `s.probed` is set (once per session) and when `lead_work_ready` is false, which leaves out queued planner rows (`PLANNER`, `dispatch.PLANNER`).
- Make a queued planner row count as Claude work for the probe. Prefer a guard of `fresh_reading`'s own over widening `lead_work_ready`, which other callers use for the lead's holds.
- Drop the once-per-session limit: the 10-minute test on the stored reading's `at` is the only limit. A probe that reads nothing is still logged and leaves the stored reading to decide; it records its own reading time only if it read something, so a failing probe could repeat each pick: after a failed probe, wait `STALE_READING` before the next one (keep the time on the session).

### Done when
- with only a planner row queued and a stored reading 11 minutes old, `fresh_reading` probes once
- with the reading 5 minutes old, it doesn't
- two calls an hour apart in one session, each with an old reading, probe twice
- after a failed probe, another call within 10 minutes doesn't probe
- with no Claude work queued, no probe (the existing test still passes)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
