---
id: f279-07-fix-next-in-line-from-tests
milestone: f279-i-would-like-to-be-able
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f279-i-would-like-to-be-able-C2757-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f279-04-next-in-line-from-the-plan's tests: Stored-plan Overview behavior has no content assertion

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f279-04-next-in-line-from-the-plan.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f279-i-would-like-to-be-able-C2757-2, blocking: in `tests/factory_dashboard/test_overview.py`.

### Finding
f279-i-would-like-to-be-able-C2757-2: Stored-plan Overview behavior has no content assertion
> The test file has no coverage for an overview with a stored queue plan. It must verify the plan-derived ticket count, sentence, ordered Next-in-line rows, exact `/queue` link, and continued fallback behavior with no plan; currently it only exercises older queue rendering.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
