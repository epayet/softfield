---
id: f6-18-priority-buttons
milestone: f6-planning-room
depends_on: [f6-17-drop-seed]
agent: lead
difficulty: 5
files:
  - runner/requests.py
  - factory_dashboard/requests.py
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/milestones.html
  - docs/adr/19-feature-board.md
  - docs/milestones/f6-planning-room.md
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
The owner reorders the work from the dashboard: each ticket in Next in line and each milestone on the Milestones page has its priority with buttons to move it up or down, and the runner applies the change at its next pick (or at once while paused).

### Context
Read "Frontmatter" and "Milestone keys" in `docs/task-format.md` (a ticket's `priority:`, a card's `**Priority:**` in its doc's header), `_ticket_rank` in `runner/dispatch.py` (lower first), `card` in `runner/milestone.py`, the request handling in `runner/requests.py` and `KINDS` in `factory_dashboard/requests.py` (protected), and the ticket rows in `factory_dashboard/templates/_partials/queue.html`.
- The owner (2026-10-07): "when will i be able to reprioritise tickets and essentially not need to do what we just did (stop runner, chat current state in terminal and replan, start runner again). this is the priority."
- **A new kind, `priority`:** subject a ticket id in `tasks/ready/` or `tasks/later/`, or a card's short key; value a whole number from 0. Applied as one commit (`f9-16-no-ollama-allowance: priority 4 → 1, by the owner`) that sets the ticket's `priority:` line, or the card's header `**Priority:**`. Refused for a ticket in `done/` or the one running (`in_flight`), or a bad value. Result: `priority of <subject> set to N`.
- **Up and down:** a ticket's ↑ sets its priority to one less than the ticket above it's (0 at least), ↓ to one more than the one below's; the same for milestones. A row shows its priority as a number beside the buttons.
- Update F6's D1 table with the new kind, and add a line under item 4 of `docs/adr/19-feature-board.md` ("Read-only at first") that reprioritising from the dashboard is now an ADR 18 request, as item 3 foresaw ("the owner changes them, on the console or the board").

### Done when
- a `priority` request on a ready ticket changes its `priority:` in one commit, and `dispatch.plan` orders it accordingly; on a card, its header's Priority; on a done or running ticket, it is refused and main is unchanged
- Next in line's ticket rows and the Milestones page's rows show each priority with ↑ and ↓ buttons posting the request
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
