---
id: f15-10-fix-wait-note-assertions-check
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_board.py
tests:
- tests/factory_dashboard/test_board.py
finding: f68-i-want-the-factory-to-be-C1080-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f15-08-card-says-what-it-waits-for's tests: Wait-note assertions check presence, not exact content

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f15-08-card-says-what-it-waits-for.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f68-i-want-the-factory-to-be-C1080-2, should-fix: in `tests/factory_dashboard/test_board.py`, line 1175.

### Finding
f68-i-want-the-factory-to-be-C1080-2: Wait-note assertions check presence, not exact content
> The board-page assertions use substring checks (`"waits for F22" in words` and `"waits for F22, F63" in words`), so unexpected extra or duplicated text can pass. Extract the card-note text and assert its exact value, as required by Done when: “the line reads ‘waits for F22, F63’, each once” (and the corresponding single-key criterion).

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
