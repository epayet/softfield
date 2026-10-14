---
id: f9-05-later-kind-column
milestone: f9-line-polish
depends_on: [f5-09-queue-button]
difficulty: 2
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/tickets.html
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
The Tickets page's Set aside table shows each ticket's kind (developer or lead) instead of its queue command.

### Context
Read the `later` section of `factory_dashboard/templates/tickets.html`, where `factory_dashboard/tickets.py` builds `later_tickets`, the Queue button f5-09 added to each row, and `tests/factory_dashboard/test_tickets.py`.
- The owner (2026-10-04): "the queue column is not useful, but the kind column could be". The `softfield queue <id>` text goes; the Queue button stays.
- A ticket's kind is its frontmatter `agent:` (no `agent:` means developer), in the words the main table's Kind column uses.

### Done when
- a lead ticket's row and a developer ticket's row each show their kind, asserted within the row; no row shows `softfield queue`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
