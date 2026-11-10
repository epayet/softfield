---
id: f231-04-seed-card-on-its-way
milestone: f231-there-are-many-bugs-in-the
difficulty: 3
depends_on: [f231-02-drop-a-set-aside-ticket]
files:
  - factory_dashboard/board.py
  - factory_dashboard/templates/board.html
tests:
  - tests/factory_dashboard/test_board.py
---

### Goal
A set-aside ticket's card in the board's Seed column shows a waiting Remove or Queue it at once: the dashed edge, and "removing" or "queuing · on its way · at the runner's next pick".

### Context
The picture to build: `.softfield/cards/f231-mockup/remove-a-set-aside-ticket.html` (Proposed, the board). Read D4 in `.softfield/cards/f231-there-are-many-bugs-in-the.md`.
- `factory_dashboard/board.py` builds a bug's card where `m["key"] == BUGS`, with `note=SET_ASIDE` in the seed stage. Its open-request reads (the `setting_aside` and `lane_requests` queries) are the example: read the open `queue` and `drop_ticket` requests by subject the same way.
- `factory_dashboard/templates/board.html`: `card_link` already draws `on-its-way` cards with a `card-way` line, for a reorder. Reuse that look; give the line the words of the request, in place of the "Set aside, won't run until you queue it" action.
- A Remove and a reorder both waiting: Remove's words win.

### Done when
- a seed bug with an open `drop_ticket` shows the dashed edge and "removing · on its way · at the runner's next pick"
- one with an open `queue` shows "queuing · on its way · at the runner's next pick"
- with neither, the card is as today
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
