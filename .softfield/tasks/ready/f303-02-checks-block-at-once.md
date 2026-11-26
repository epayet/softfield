---
id: f303-02-checks-block-at-once
milestone: f303-from-a-factory-suggestion-add-a
difficulty: 3
depends_on: [f303-02-size-blocks-at-once]
files:
  - runner/lead_job.py
tests:
  - tests/runner/test_loop.py
agent: lead
area: factory
---

## Goal
When a lead ticket's check-all fails `size` or `imports`, block it at once with the same reason a developer ticket gets, instead of stepping up or blocking it as "check-all failed" (ADR 55 item 6, for lead tickets).

## Context
- `.softfield/adr/55-a-file-at-its-size-limit-is-split-by-plan.md` item 6 and D5 in `.softfield/cards/f303-from-a-factory-suggestion-add-a.md`.
- `runner/lead_job.py`: the lead ticket's settling reads check-all's failures (`_check_results`) and, on a failure, may step up before it calls `block` with "check-all failed; the work is on …"; when `size` or `imports` is among the failures, call `block` with the reason f303-02-size-blocks-at-once built in `runner/developer_job.py` (reuse it, don't write it twice), with no step-up.
- `tests/runner/test_loop.py`: the lead-ticket tests that drive `work_queue` are the example.

## Done when
- a lead ticket whose check-all fails `size` is blocked with the size reason, is not stepped up, and its work stays on its branch
- the same for `imports`
- a lead ticket that fails another check behaves as today
- the listed `tests:` pass, and fail without the change
- all gates pass
