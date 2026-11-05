---
id: f69-12-fix-radius-test-dead-code-tests
milestone: f69-i-want-a-button-to-switch
agent: lead
area: factory
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1826-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f69-10-fix-radius-test-dead-code's tests: Radius regression test does not prove it rejects a stray radius

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f69-10-fix-radius-test-dead-code.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1826-2, should-fix: in `tests/factory_dashboard/test_app.py`, line 3564.

### Finding
f69-i-want-a-button-to-switch-C1826-2: Radius regression test does not prove it rejects a stray radius
> The Done when says “a test shows it, on a CSS string with a stray radius,” but this test only reads the current dashboard.css; it would not catch a broken or inert check while that stylesheet remains clean. Also, it skips an entire rule whenever its body contains border-radius: 0, even if the same rule has a nonzero radius declaration, so that stray radius can pass.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
