---
id: f1-48-ticket-work-split
milestone: f1
depends_on: [f1-49-heartbeat]
difficulty: 3
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/ticket.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
`/tickets/{id}` shows who did the work on that ticket: each agent's part, with its jobs, time, tokens or dollars, and who merged it.

### Context
Read `factory_dashboard/tickets.py` (`get_ticket`, `ticket_jobs`), `factory_dashboard/templates/ticket.html` and `tests/factory_dashboard/test_tickets.py`; f1-10's spec is `tasks/done/f1-10-ticket-pages.md`. `write_fixture`, `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py` stay untouched; put new rows in your own function in `tests/factory_dashboard/conftest.py` (extend `write_tickets`).
- Facts: every job row has its `agent` and `role` (`developer`, `last-attempt`, `direction`, `escalation`, `checkpoint`, `lead-ticket`, `review`); the ticket row has `merged_by`. Local jobs have tokens and no dollars (`cost_usd` is empty); Claude jobs have `cost_usd`.
- **A "Who did the work" section**, above the jobs list, with one row per agent:
  - its roles on this ticket (for example "developer ×3, last-attempt")
  - its job count, minutes, tokens in, and dollars (or "–")
  - "merged" next to the agent that merged it

  For example, f1-15 had local Qwen with 5 attempts and Claude with a direction and 2 escalations.
- Order: the merging agent first, then by minutes. A ticket with no jobs has no section.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and read the cells of the section, not just that the text appears somewhere on the page.

### Done when
- a ticket worked by a local agent and Claude shows two rows with their roles, counts, minutes, tokens and dollars, the merger first and marked "merged"
- a ticket with no jobs shows no section
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1369
gate_failures: []
tokens: 1976279
```
