---
id: f233-01-direction-is-the-leads
milestone: f233-why-is-the-factory-not-doing
difficulty: 2
depends_on: []
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
On the board's developer's view, a developer ticket waiting for the lead's direction counts as the lead's work, so the board never says developers can work when they can't.

### Context
Read "What happened" and D1 in `.softfield/cards/f233-why-is-the-factory-not-doing.md`.

After two failed attempts the runner queues a `direction` job for the lead: a row in `work_queue` with `kind = 'direction'`, `subject` = the ticket's id and `done IS NULL` while it waits (`metrics.open_jobs` in `runner/metrics.py` reads them). The ticket itself stays `ready`. `board()` in `factory_dashboard/board.py` never reads these rows, so `_dev_work` counts the ticket in `now`, the card is lit, and `Board.developers` ("Developers can work on N cards, M tickets") counts it.

Follow the escalated case (`with_lead`, F206 D3): `_dev_work` and `_dev_resolver` get the set of ticket ids with an open direction, read once in `board()`. Example to copy: `test_an_escalated_dev_ticket_reads_tried_and_now_with_the_lead` in `tests/factory_dashboard/test_board.py`.

Words, in `dev_tag` of `factory_dashboard/templates/board.html`: "developers tried <ticket> · waits for the lead's direction". The escalated wording "· now with the lead" doesn't change.

### Done when
- a ready developer ticket with an open `direction` row is not counted in `now` or `after`, nor in `Board.developers`
- a card whose only developer work is such a ticket is not lit (`dev-can`), and reads "developers tried f72-01 · waits for the lead's direction"
- a ready developer ticket that depends on one waiting for its direction counts as waiting, and names it in `waits_for`
- once the `direction` row is done, the ticket counts as it does today
- a card with one ticket waiting for its direction and another developers can take now stays lit and counts only the second
- the listed `tests:` pass, and fail without the change
