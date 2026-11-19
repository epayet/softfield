---
id: f265-06-fix-tiles-refresh-tests-tests
milestone: f265-the-factory-now-section-in-planning
agent: lead
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f265-the-factory-now-section-in-planning-C2513-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f265-04-fix-tiles-refresh-tests's tests: The live tile test does not verify gauge content changes or a reload-free poll

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f265-04-fix-tiles-refresh-tests.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f265-the-factory-now-section-in-planning-C2513-2, should-fix: in `tests/factory_dashboard/test_planning.py`, line 1289.

### Finding
f265-the-factory-now-section-in-planning-C2513-2: The live tile test does not verify gauge content changes or a reload-free poll
> The test only asserts that the `#lead-window` text contains the words "5-hour window" and "week" after a job starts; it does not seed and change allowance/gauge values and verify the bars or percentages update. It also treats an unchanged URL as proof of no reload, despite not tracking navigations or reloads. Thus it would miss stale gauge content or a navigation/reload, contrary to: "The browser test verifies the factory tile but not the lead-window refresh or reload-free behavior."

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
