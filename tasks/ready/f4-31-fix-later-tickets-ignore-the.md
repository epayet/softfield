---
id: f4-31-fix-later-tickets-ignore-the
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- factory_dashboard/tickets.py
tests:
- tests/factory_dashboard/test_tickets.py
finding: f4-always-on-C292-1
---

### Goal
Fix a checkpoint finding on f4-18-later-list: Later tickets ignore the current ticket filter

### Context
A should-fix finding (f4-always-on-C292-1) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-18-later-list.md`: in `factory_dashboard/tickets.py`. What it found is under Finding.

### Finding
> tickets_page passes milestone/state through to list_tickets, but list_later_tickets ignores both arguments and always renders every project-level later ticket. A filtered /tickets?milestone=... or /tickets?state=... page still shows unrelated later tickets, so the panel does not match the list and can expose the wrong tickets.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
