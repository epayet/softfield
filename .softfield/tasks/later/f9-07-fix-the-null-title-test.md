---
id: f9-07-fix-the-null-title-test
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_line.py
tests:
- tests/factory_dashboard/test_line.py
finding: f9-line-polish-C420-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f3-28-floor-words's tests: The null-title test does not assert the row contains only its key.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f3-28-floor-words.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f9-line-polish-C420-2, should-fix: in `tests/factory_dashboard/test_line.py`, `test_a_planted_row_with_null_title_says_its_key_alone`.
- The row's name is drawn by `row` in `factory_dashboard/static/factory.js`: the key in capitals, then " · " and the title only when there is one.

### Finding
f9-line-polish-C420-2: The null-title test does not assert the row contains only its key.
> The assertions that the text starts with F1 and lacks the separator still allow extra text after the key, so a row that does not say the key alone could pass. Assert the exact expected text to check the requested content.

### Done when
- the test asserts the row's whole name equals "F1", so "F1 null", "F1 ·" or "F1 · None" would fail it
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
