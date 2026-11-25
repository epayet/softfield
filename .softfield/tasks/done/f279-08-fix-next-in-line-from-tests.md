---
id: f279-08-fix-next-in-line-from-tests
milestone: f279-i-would-like-to-be-able
agent: lead
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f279-i-would-like-to-be-able-C2762-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f279-06-fix-next-in-line-from's tests: Stored-plan test only partially checks row content and link destination

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f279-06-fix-next-in-line-from.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f279-i-would-like-to-be-able-C2762-1, should-fix: in `tests/factory_dashboard/test_overview.py`, line 1770.

### Finding
f279-i-would-like-to-be-able-C2762-1: Stored-plan test only partially checks row content and link destination
> The f279-06 test checks one row and only substring presence for its text. It does not verify the ticket title, exact ticket/project link, row ordering among multiple rows, or that the whole-queue anchor has href="/queue"; the stripped `section(...)` text also masks any wrong link destination.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
