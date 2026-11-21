---
id: f275-03-fix-start-plate-on-top-tests
milestone: f275-a-project-created-by-web-interface
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_projects.py
tests:
- tests/factory_dashboard/test_projects.py
finding: f275-a-project-created-by-web-interface-C2611-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f275-02-start-plate-on-top's tests: The Start-it test does not check that the new plate is prepended

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f275-02-start-plate-on-top.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f275-a-project-created-by-web-interface-C2611-3, should-fix: in `tests/factory_dashboard/test_projects.py`, line 470.

### Finding
f275-a-project-created-by-web-interface-C2611-3: The Start-it test does not check that the new plate is prepended
> `test_start_it_sends_the_forms_json_and_shows_the_plate_at_once` verifies the plate's contents and request but never verifies it is the first list item, before waiting plates and project rows, as required by f275. The test must compare `#order-form .rank` first element/plate position after clicking Start it.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 787
gate_failures: []
tokens: 279916
```
