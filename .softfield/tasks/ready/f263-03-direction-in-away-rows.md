---
id: f263-03-direction-in-away-rows
milestone: f263-on-the-console-run-you-can
difficulty: 3
depends_on: [f263-02-direction-in-now]
files:
  - factory_dashboard/queries.py
  - factory_dashboard/templates/_partials/away.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
In the Overview's While you were away, a merged ticket that had the lead's direction keeps it, folded under its title.

### Context
- The picture to build: the Proposed "Phone · While you were away" frame of `.softfield/cards/f263-mockup/direction-on-overview.html`. Decisions D2 and D3 in `.softfield/cards/f263-on-the-console-run-you-can.md`.
- The text is in `jobs.direction` (f263-01). In `away` (`factory_dashboard/queries.py`), give each `AwayTicket` the newest `direction` job of its ticket that has a `direction`: its text, its job id, its cost, and the attempt it came before (the ticket's developer attempts started before it, plus one).
- In `factory_dashboard/templates/_partials/away.html`, after the row's title, draw the same `details.direction` plate f263-02 drew for Now (reuse its CSS), with "Opus · before attempt N" in its summary and no first line; opened, the whole text through `_to_html` in `factory_dashboard/milestones.py` and the link to `/jobs/<id>` with its cost.

### Done when
- a merged ticket with a stored direction shows the folded plate in its away row; opened, the whole text, escaped, and the job link
- a merged ticket without one looks as it does today
- the plate also shows when the span is changed in place (the replay bar's select redraws the panel)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
