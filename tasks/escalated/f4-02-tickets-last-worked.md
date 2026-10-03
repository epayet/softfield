---
id: f4-02-tickets-last-worked
milestone: f4-always-on
depends_on: []
difficulty: 2
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/tickets.html
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
The Tickets page lists the most recently worked tickets first, and says when each was last worked.

### Context
Read `factory_dashboard/tickets.py` (`list_tickets`, `TicketRow`), `factory_dashboard/templates/tickets.html` and the list tests in `tests/factory_dashboard/test_tickets.py` (the `tickets_client` fixture in `tests/factory_dashboard/conftest.py`).
- Facts: `list_tickets` sorts by `COALESCE(m.started, '') DESC, t.id DESC`, the milestone's start then the row id, so a ticket worked a minute ago can sit far down. The header says "newest first".
- "Last worked" is the latest `started` of the ticket's jobs (`jobs.ticket_id`). A ticket with no job yet sorts after every worked one, newest row first among them.
- Show it as a "Last worked" column with the same `ago` filter the other pages use ("12 min ago"), "–" for none. The header becomes "latest work first".

### Done when
- of two tickets, the one whose latest job started later is listed first, whatever their milestones
- a ticket with no jobs is listed after every ticket with one, and its Last worked cell reads "–"
- the Last worked cell of a worked ticket reads its age, asserted within that ticket's row
- the milestone and state filters still work
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: invalid
attempts: 1
tokens: 40639
logs: var/runs/20261003-071707/f4-02-tickets-last-worked
```
