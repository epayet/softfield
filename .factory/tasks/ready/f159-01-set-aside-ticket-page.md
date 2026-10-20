---
id: f159-01-set-aside-ticket-page
milestone: f159-there-s-a-bug-set-aside
agent: developer
difficulty: 4
depends_on: []
files:
  - factory_dashboard/tickets.py
  - factory_dashboard/board.py
  - factory_dashboard/templates/ticket.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_tickets.py
  - tests/factory_dashboard/test_board.py
---

### Goal
A set-aside ticket's page says it won't run until the owner queues it and has a "Queue it" button; its board card says so too, and every ticket's page shows its Goal and Done when as text, without the front matter.

### Context
The picture to build: `.factory/cards/f159-mockup/set-aside-ticket.html` (Proposed). Decisions D1–D4 in `.factory/cards/f159-there-s-a-bug-set-aside.md`.
- The example to follow for the button: the Queue button in the Set aside table of `factory_dashboard/templates/tickets.html`. It posts the `queue` request (`runner/requests.py`, `QUEUE`) to `/requests` with `hx-post`; post the same, with the same `kind`, `project` and `subject`. Change nothing in `runner/`.
- A set-aside ticket is one whose state is `later` (`get_ticket` and `ticket_page` in `factory_dashboard/tickets.py`). While an open `queue` request names the ticket (`metrics.open_requests` in `runner/metrics.py`), the plate shows "Queue it · on its way · at the runner's next pick" instead of the button, also after a reload.
- The board card's note is `SET_ASIDE` in `factory_dashboard/board.py`; it moves from `card-note` to the `card-action` look in `factory_dashboard/templates/board.html`, as the mock-up draws it.
- The ticket body is the whole file: front matter between `---` lines, then `### Goal`, `### Context`, `### Done when`. Show Goal as a paragraph, Done when as a list, Context inside a closed `<details>` titled "The lead's notes for the agent". A body without those headings shows as it does today.
- The plate's look uses only the tokens at the top of `factory_dashboard/static/dashboard.css` (hazard stripe on the plate header, corner ticks in the ink); it adds no colour.

### Done when
- `/tickets/<id>` for a ticket in state `later` shows first a "Set aside" panel reading "This ticket won't run until you queue it." and a "Queue it" button that posts a `queue` request for that ticket
- with an open `queue` request for it, the panel shows "on its way · at the runner's next pick" and no button
- a ticket in any other state has no such panel, and its State pill reads its state; `later` reads "set aside"
- the page shows no front-matter line (`id:`, `priority:`…); Goal and Done when show as text, Context folded
- on the board, a set-aside bug card reads "Set aside, won't run until you queue it ›"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
