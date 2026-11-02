---
id: bug-47-planning-row-tests-read-their-row
milestone: bugs
difficulty: 2
depends_on: []
area: factory
priority: 75
finding: f6-planning-room-C542-1
tests_only: true
files:
  - tests/factory_dashboard/test_overview.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's planning-row tests read the row's `title` within that row, not from everything after "Next in line".

### Context
Read the planning-row tests in `tests/factory_dashboard/test_overview.py` (lines 2760–2850: the long-text one and `test_planning_row_with_empty_text_shows_first_comment`). They find the `title` with a regex over all the HTML after "Next in line", so another row's `title` could match. The code is right.
- Cut the row out first, as `planning_row` already is, and read its `title` there.

### Done when
- each test reads `title` from the `<div class="next-row">` that holds "Planning:", and from nowhere else
- a second queued row with its own `title` placed before the planning row doesn't change what the tests read
- every assertion they have today is kept
- all gates pass (see `docs/workflow.md`)
