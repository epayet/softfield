---
id: f4-32-fix-later-panel-tests-only
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_tickets.py
tests:
- tests/factory_dashboard/test_tickets.py
finding: f4-always-on-C292-2
---

### Goal
Fix a checkpoint finding on f4-18-later-list: Later-panel tests only assert strings are present somewhere

### Context
A should-fix finding (f4-always-on-C292-2) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-18-later-list.md`: in `tests/factory_dashboard/test_tickets.py`. What it found is under Finding.

### Finding
> The test checks that the ticket id, title, and queue command appear anywhere inside the later section, but it never confirms they are in the same row or that the row contains the correct link and command in the correct cells. This would let a malformed template pass and mask the actual bug.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
