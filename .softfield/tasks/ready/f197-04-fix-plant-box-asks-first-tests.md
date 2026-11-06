---
id: f197-04-fix-plant-box-asks-first-tests
milestone: f197-reverse-plant-and-plant-and-ask
agent: lead
difficulty: 1
depends_on: []
files:
- tests/factory_dashboard/test_planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f89-does-allowance-refresh-at-the-beginning-C1903-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f197-03-fix-plant-box-asks-first-tests's tests: Plant-button tests do not enforce the required helper text or per-button ask value

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f197-03-fix-plant-box-asks-first-tests.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1903-1, should-fix: in `tests/factory_dashboard/test_planning.py`, line 2121.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1903-1: Plant-button tests do not enforce the required helper text or per-button ask value
> No test checks that the accompanying line exactly reads “Plant and ask the lead: the lead answers it on its thread. Plant: a seed card that waits for you; write on its thread to send it to the lead.” The onclick assertions search the whole HTML independently of each button, so swapped handlers could pass; check each button’s submitted ask value is false or true, respectively.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
