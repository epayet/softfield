---
id: f4-32-fix-later-panel-tests-only
milestone: f4-always-on
difficulty: 3
depends_on: []
files:
- factory_dashboard/templates/tickets.html
- tests/factory_dashboard/test_tickets.py
tests:
- tests/factory_dashboard/test_tickets.py
finding: f4-always-on-C292-2
---

### Goal
Fix a checkpoint finding on f4-18-later-list: Later-panel tests only assert strings are present somewhere

### Context
A should-fix finding (f4-always-on-C292-2) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f4-18-later-list.md`: in `tests/factory_dashboard/test_tickets.py`. What it found is under Finding.
- Facts: the Later panel's row in `factory_dashboard/templates/tickets.html` (the `{% for t in later_tickets %}` loop) already renders the id link, title and queue command in one row, so a test-only change passes on main and fails the `tests-fail-on-main` gate. The fix is to name the row and its cells in the template, and test through those names.
- Pattern to follow: the agent-work table in `factory_dashboard/templates/ticket.html` puts `data-col="…"` on each `<td>`, and `agent_row` in `tests/factory_dashboard/test_tickets.py` reads a row's cells into a dict by `data-col`.

### Finding
> The test checks that the ticket id, title, and queue command appear anywhere inside the later section, but it never confirms they are in the same row or that the row contains the correct link and command in the correct cells. This would let a malformed template pass and mask the actual bug.

### Done when
- each Later row in `tickets.html` carries `data-ticket="<id>"` on its `<tr>`, and its three cells carry `data-col="id"`, `data-col="goal"` and `data-col="queue"`; nothing else in the template changes
- `test_later_tickets_panel_shows_ticket_with_title_and_queue_command` finds the `f1-99-later` row by `data-ticket` and asserts each cell's content by `data-col`: the id cell holds the link `href="/tickets/f1-99-later"` with text `f1-99-later`, the goal cell is `A set-aside ticket.`, the queue cell holds `uv run runner queue f1-99-later`
- the listed `tests:` pass, and fail without the template change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 2014
gate_failures: ['tests-fail-on-main', 'stopped']
tokens: 591007
```
