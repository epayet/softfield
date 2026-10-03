---
id: f4-29-fix-queue-reason-tests-do
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- coucou/tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-5
---

### Goal
Fix a checkpoint finding on f4-08-queue-waits-for: Queue reason tests do not verify the reason in the target ticket’s row

### Context
A should-fix finding (f4-always-on-C231-5) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-08-queue-waits-for.md`: in `coucou/tests/factory_dashboard/test_overview.py`, line 383. What it found is under Finding.

### Finding
> The dependency, escalation, and Claude-wait tests check only whether a phrase appears anywhere in the queue section. They can pass when the phrase is attached to a different ticket, so they do not establish the required per-row content; the existing queue_rows helper is not used for these assertions.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
