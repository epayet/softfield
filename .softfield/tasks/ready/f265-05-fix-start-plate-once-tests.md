---
id: f265-05-fix-start-plate-once-tests
milestone: f265-the-factory-now-section-in-planning
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_projects.py
tests:
- tests/factory_dashboard/test_projects.py
finding: f265-the-factory-now-section-in-planning-C2513-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f122-06-start-plate-once's tests: The Start-it browser test does not prove polling adds only one plate

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f122-06-start-plate-once.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f265-the-factory-now-section-in-planning-C2513-1, should-fix: in `tests/factory_dashboard/test_projects.py`, line 468.

### Finding
f265-the-factory-now-section-in-planning-C2513-1: The Start-it browser test does not prove polling adds only one plate
> It waits for the Asked response and verifies fields, but never asserts that `#order-form .proj-asked` contains exactly one plate after polling. This would not catch duplicate plate appends on repeated `htmx:beforeRequest` events, contrary to the Goal: "Pressing \"Start it\" ... draws the new project's on-its-way plate once, however long the request waits."

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
