---
id: f6-26-fix-tests-bless-the-broken
milestone: f6-planning-room
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f6-planning-room-C529-2
tests_only: true
---

### Goal
Fix a checkpoint finding on f6-15-queue-message's tests: Tests bless the broken link and do not consistently assert row content.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f6-15-queue-message.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f6-planning-room-C529-2, should-fix: in `tests/factory_dashboard/test_overview.py`, line 1499.

### Finding
f6-planning-room-C529-2: Tests bless the broken link and do not consistently assert row content.
> The link assertion expects `/planning/F11` instead of the required `/planning/f11`, so it passes with a link that cannot load the thread. The empty-text comment and plant tests only search the whole Next in line section for text; they should assert the normalized, entity-unescaped text within the specific row, as the ticket's Done when requires.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
