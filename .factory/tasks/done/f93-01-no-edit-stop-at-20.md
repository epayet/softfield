---
id: f93-01-no-edit-stop-at-20
milestone: f93-is-no-edit-after-10-minutes
depends_on: []
agent: lead
difficulty: 1
priority: 0
area: factory
files:
  - runner/local_model.py
tests:
  - tests/runner/test_local_model.py
---

### Goal
A developer attempt is stopped for making no edit after 20 minutes instead of 10, so an attempt that is about to write its first edit is no longer thrown away.

### Context
Read F93's "What we know" and Decisions D1–D2 in `.factory/cards/f93-is-no-edit-after-10-minutes.md`. In `runner/local_model.py`: `NO_EDIT_AFTER`, `STOP_NO_EDIT`, `stuck` and the comment above them. In `tests/runner/test_local_model.py`: `_ticking`, `test_a_stream_with_no_edit_for_10_minutes_is_stopped` and `test_a_stream_that_edits_at_minute_9_runs_on`, whose frames end at minute 20.
- The stop's words are built from `NO_EDIT_AFTER` (D2): nothing else in the code spells the number of minutes.
- The repeat stop (`STOP_REPEATING`) and the attempt's own limit (`[timeouts] opencode`) don't change.
- Session reports and job rows already written keep "10 min"; nothing reads them back by that text.

### Done when
- an attempt with no edit is stopped at minute 20 with "stopped: no edit after 20 min", in its result and in its log's marker; at minute 19 it still runs
- an attempt whose first edit comes at minute 19 runs on to its end
- the two tests above are renamed for the new minutes, and no test spells the stop's words without also comparing them to `STOP_NO_EDIT`
- the comment above `NO_EDIT_AFTER` says why 20: F93, 16 of 29 attempts stopped at 10 minutes while first edits came as late as 9.2
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
