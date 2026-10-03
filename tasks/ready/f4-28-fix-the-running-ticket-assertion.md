---
id: f4-28-fix-the-running-ticket-assertion
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- coucou/tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C231-4
---

### Goal
Fix a checkpoint finding on f4-08-queue-waits-for: The running-ticket assertion can pass when the forbidden row is present

### Context
A should-fix finding (f4-always-on-C231-4) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-08-queue-waits-for.md`: in `coucou/tests/factory_dashboard/test_overview.py`, line 373. What it found is under Finding.

### Finding
> The condition allows f1-04-live to appear whenever “waits for f1-04-live” occurs anywhere in the queue. That dependency text is expected from another row, so this assertion can pass even if the running ticket is incorrectly listed. The other queue checks also search section-wide text rather than the target row, and the ordering test skips its assertion if either group is absent.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
