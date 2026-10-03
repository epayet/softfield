---
id: f4-27-fix-the-queue-fixture-does
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- coucou/tests/factory_dashboard/conftest.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-3
---

### Goal
Fix a checkpoint finding on f4-08-queue-waits-for: The queue fixture does not include the running ticket it claims to seed

### Context
A should-fix finding (f4-always-on-C231-3) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-08-queue-waits-for.md`: in `coucou/tests/factory_dashboard/conftest.py`, line 260. What it found is under Finding.

### Finding
> queue_client starts from db_path, which calls write_fixture only, then calls write_queue. Neither creates f1-04-live or a running job for it; the comment that it is already in write_fixture is inaccurate. Consequently, the exclusion test does not exercise a ticket with a running job, and the dependency fixture refers to an unknown ticket instead.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
