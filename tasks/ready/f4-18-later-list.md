---
id: f4-18-later-list
milestone: f4-always-on
depends_on: [f4-09-later-folder]
difficulty: 3
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/templates/tickets.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_tickets.py
---

### Goal
The Tickets page has a "Set aside" panel above the list: the tickets in `tasks/later/`, each with its goal and the command that queues it again.

### Context
Read `factory_dashboard/tickets.py` (`list_tickets`, `tickets_page`), `factory_dashboard/templates/tickets.html` and `tests/factory_dashboard/test_tickets.py`.
- Facts (f4-09): the runner records the tickets in `tasks/later/` with `tickets.state = 'later'`. The command that brings one back is `uv run runner queue <ticket id>`.
- The panel lists each later ticket's id (linked to its page), its title and that command in a `<code>`. With none, the panel isn't shown.
- Put your new fixture rows in your own function in `tests/factory_dashboard/conftest.py`.

### Done when
- a ticket with state `later` appears in the panel with its title and `uv run runner queue <its id>`, asserted within its row
- with no later tickets, there is no panel
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
