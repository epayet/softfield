---
id: f303-02-size-blocks-at-once
milestone: f303-from-a-factory-suggestion-add-a
difficulty: 4
depends_on: [f303-04-imports-at-top]
files:
  - runner/developer_job.py
tests:
  - tests/runner/test_loop.py
agent: lead
area: factory
---

## Goal
When a developer attempt fails the `size` or `imports` gate, block the ticket at once with a reason that says what must be planned, instead of retrying, directing or escalating it (ADR 55 item 6, for developer tickets).

## Context
- `.softfield/adr/55-a-file-at-its-size-limit-is-split-by-plan.md` item 6 and D5 in `.softfield/cards/f303-from-a-factory-suggestion-add-a.md`: when it applies and the reason's wording.
- `runner/developer_job.py`: `run_task` runs the gates each attempt and keeps the first failure in `failed`; when the attempt's `size` or `imports` result failed, whatever else failed, end the attempt and call `block` with the reason, the branch kept as it is.
- `block` (`runner/developer_job.py`) already queues the lead's look on the card's thread (ADR 29): nothing to add there.
- `tests/runner/test_loop.py`: tests that drive `work_queue` with a fake model and gates are the example (`test_retry_gets_gate_output_and_a_hint_and_can_recover`).
- Lead tickets are `f303-02-checks-block-at-once`'s, not this one's.

## Done when
- a developer attempt whose `size` gate fails is not retried: the ticket is in `.softfield/tasks/blocked/` after one attempt, its reason names the file, its lines and the limit and says it needs a planned split, and no direction or escalation was queued
- the same for `imports`, with a reason naming the file, the line and the module and saying it needs a planned move of the shared code
- an attempt that fails only another gate still retries as today
- the work stays on the ticket's branch
- the listed `tests:` pass, and fail without the change
- all gates pass
