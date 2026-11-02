---
id: f15-07-arrows-go
milestone: f15-reprioritising-tickets
difficulty: 3
depends_on: [f15-05-replan]
agent: lead
commands: [rm factory_dashboard/templates/_partials/move.html]
files:
  - factory_dashboard/templates/_partials/queue.html
  - factory_dashboard/templates/milestones.html
  - factory_dashboard/templates/_partials/move.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/line.py
  - factory_dashboard/milestones.py
  - factory_dashboard/queries.py
  - factory_dashboard/overview.py
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_overview.py
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_board.py
---

### Goal
The ↑ and ↓ arrows leave Next in line and the Milestones page: the board is the one place the owner reorders.

### Context
Read `.softfield/cards/f15-reprioritising-tickets.md` (D8 and the Replan). The owner (2026-10-13): "I'm actually not a fan of the arrows in overview and plan to kill them."
- **The arrows:** `factory_dashboard/templates/_partials/move.html` (`.move`, `.move-button`, the `#move-<subject>` status), included by `factory_dashboard/templates/_partials/queue.html` (each ticket's `.next-row` under "Next in line") and `factory_dashboard/templates/milestones.html` (the priority cell of each card's row). Their CSS: `.move`, `.move-button`, `.move-status .request` in `factory_dashboard/static/dashboard.css`.
- **What only serves them:** `up` and `down`, set in `factory_dashboard/line.py` (the loop after `tickets_next`, "the priorities its ↑ and ↓ ask for") and in `_with_moves` of `factory_dashboard/milestones.py` (`MilestoneRow.up`, `.down`), both from `queries.moves` in `factory_dashboard/queries.py`. `_with_moves` also sets `priority` on each row: keep that, drop `up` and `down` (rename it for what is left), and remove `queries.moves` once nothing calls it.
- Each row still shows its priority as a number: "priority 100" on Next in line, the number in the Milestones cell (– when none).
- Next in line gets one link, "Reorder on the board ›", to `/board{{ q }}`.
- The Queue panel's "Drain it with <code>{{ drain }}</code>" goes, a terminal command on a dashboard page (the owner, 2026-10-13): it says "N tickets waiting." alone. Drop the `"drain"` entry the overview page is given in `factory_dashboard/overview.py` (`_drain` itself stays: the "Needs you" queue item uses it), and turn `test_now_holds_what_works_then_next_in_line_and_the_command_that_drains_it` in `tests/factory_dashboard/test_overview.py` into a check that no `softfield run` shows there.
- The board says nothing about arrows on the page; two leftovers name them: the Jinja comment above "All milestones and their trends ›" in `factory_dashboard/templates/board.html`, and the docstring of `test_the_board_replaces_the_milestones_tab_and_links_to_the_list` in `tests/factory_dashboard/test_board.py`. Both lose the "↑ and ↓".
- **The tests that pressed the arrows:** `test_next_in_line_shows_each_priority_with_buttons_that_move_it`, `test_next_in_line_follows_the_priorities_the_runner_reads` (it reads the order through the `_moves` helper) and `test_a_priority_at_0_has_no_up_button` in `tests/factory_dashboard/test_overview.py`; `test_each_milestone_not_done_shows_its_priority_with_buttons_that_move_it` in `tests/factory_dashboard/test_milestones.py`. Keep what they check of the order and the numbers.
- The `priority` request and the runner's side of it stay (`tests/factory_dashboard/test_requests.py` still posts one): a ticket's own priority is still set from the console and by the lead.
- A lead ticket because a developer's tools can't remove a file.

### Done when
- Next in line and the Milestones page hold no `move-button` and post no `priority` request
- each row still shows its priority, and Next in line keeps the runner's order
- Next in line links to the board, and the Queue panel holds no `<code>`
- `factory_dashboard/templates/_partials/move.html` is gone and nothing includes it; `queries.moves`, the `up` and `down` fields and the `.move*` CSS are gone
- the tests that pressed the arrows are replaced by tests of the above
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
