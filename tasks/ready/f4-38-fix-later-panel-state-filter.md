---
id: f4-38-fix-later-panel-state-filter
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- factory_dashboard/tickets.py
- tests/factory_dashboard/test_tickets.py
tests:
- tests/factory_dashboard/test_tickets.py
finding: f4-always-on-C19-1
---

### Goal
The "Set aside" panel on `/tickets` lists only tickets in state `later`, whatever the `state` filter says; the milestone filter still narrows it.

### Context
Read `list_later_tickets` and `tickets_page` in `factory_dashboard/tickets.py`, and `test_filter_by_state_shows_only_matching` in `tests/factory_dashboard/test_tickets.py`.
- Facts: `tickets_page` passes `state` to `list_later_tickets`, which then uses it instead of `later`. So `/tickets?state=escalated` fills the panel titled "Set aside" with the escalated tickets, each with a `uv run runner queue` command, duplicating the main table.
- The test hid it: it counts rows with the regex `<tr>`, and since f4-32 the panel rows are `<tr data-ticket=…>`, so they are not counted. Its comment ("the later panel … is absent") is false today.
- `later_client` in `tests/factory_dashboard/conftest.py` has a `later` ticket plus others; use it.

### Done when
- `/tickets?state=escalated` has no ticket of state `escalated` inside the `later` section (the section is absent when no `later` ticket matches the milestone)
- `/tickets?state=later` shows the `later` tickets in the panel; `/tickets?milestone=m4` still narrows the panel to that milestone's `later` tickets
- a test requests a non-`later` state filter against a page with both an escalated and a `later` ticket, and checks the escalated ticket is not in the `later` section; the weak `?state=done` test asserts something that would fail on a panel listing `done` tickets
- `test_filter_by_state_shows_only_matching` counts all `<tr` rows of the page body (panel rows included), so a leaking panel fails it
- the listed `tests:` pass, and fail without the change
- all gates pass
