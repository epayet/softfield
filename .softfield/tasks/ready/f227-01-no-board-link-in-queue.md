---
id: f227-01-no-board-link-in-queue
milestone: f227-the-reorder-from-the-board-link
difficulty: 1
depends_on: []
files:
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Queue panel no longer has its "Reorder on the board ›" link, and with nothing waiting it shows no "Next in line" heading over an empty list.

### Context
The picture to build: `.softfield/cards/f227-mockup/queue-link.html`. Decisions: D1 and D2 in `.softfield/cards/f227-the-reorder-from-the-board-link.md`.
- `factory_dashboard/templates/_partials/queue.html` draws the panel, for the page and for its live refresh.
- `tests/factory_dashboard/test_overview.py` asserts the link in `test_another_project_shows_only_its_own`, `test_next_in_line_says_what_a_parked_review_waits_for` and `test_next_in_line_shows_each_priority_and_sends_reordering_to_the_board`, and the heading on an empty queue in `test_empty_queue_shows_message_once`. Rework them to what this ticket asks.
- A review due with no ticket or job waiting is still a row, so the list's condition counts the fast lane, the queued jobs and `next`, not the ticket count.

### Done when
- `/` and `/live` have no "Reorder on the board" with tickets waiting, nor with the queue empty
- `/?project=<another project>` still has the Board tab, linking to `/board?project=<that project>`
- with nothing waiting, the panel says "The queue is empty." and has neither "Next in line" nor a `belt` list
- with only a queued job, or only a due review, "Next in line" and its row still show
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
