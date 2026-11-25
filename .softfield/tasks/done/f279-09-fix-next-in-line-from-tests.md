---
id: f279-09-fix-next-in-line-from-tests
milestone: f279-i-would-like-to-be-able
agent: lead
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f279-i-would-like-to-be-able-C2762-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f279-07-fix-next-in-line-from-tests's tests: No-plan fallback test is too presence-based

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f279-07-fix-next-in-line-from-tests.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f279-i-would-like-to-be-able-C2762-2, blocking: in `tests/factory_dashboard/test_overview.py`, line 1782.

### Finding
f279-i-would-like-to-be-able-C2762-2: No-plan fallback test is too presence-based
> The f279-07 test only checks generic strings "tickets waiting" and "Next in line" plus absence of "Over pace.". It does not assert the exact fallback count, exact older queue rows or their order, or preserve the fallback's exact link/text behavior, so it can pass despite incorrect fallback content.

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
