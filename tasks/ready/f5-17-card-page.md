---
id: f5-17-card-page
milestone: f5-board
depends_on: [f5-14-factory-look, f5-15-board-data, f5-16-board-page, f5-08-signoff-button]
agent: lead
difficulty: 4
files:
  - factory_dashboard/board.py
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/board.html
  - factory_dashboard/templates/base.html
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_board.py
---

### Goal
A milestone's page becomes its card's page: its stage, priority and area at the top, how far it has grown, and its tickets in run order with who works on each and which are set aside.

### Context
Read `docs/milestones/f5-board-mockup/Card.dc.html` (the picture: read its markup and the data in its script), `factory_dashboard/milestones.py` (the `/milestones/{key}` route), `factory_dashboard/templates/milestone.html`, `factory_dashboard/board.py` (the stages, f5-15), `run_order` in `factory_dashboard/queries.py` and `tests/factory_dashboard/test_milestones.py`.
- **The header:** the stage's icon and name, the priority, the area, and tickets done of total. The stage is the board's (f5-15), not the doc's state. Keep what the page shows today below it (the sign-off sheet, numbers, the Sign off button from f5-08).
- **"How it grew":** the six stages in a row, the card's own one lit and the later ones dimmed. Show dates only where the database has them: `milestones.started` on growing, `milestones.ended` on harvested.
- **The tickets:** in the runner's order (`run_order` for the ready ones: priority, then id), each with its goal, who did or will do it (the last job's agent, else "the lead" or "a developer" from `tickets.kind`) and its state. Set-aside ones (state `later`) read "set aside"; removed ones are left out.
- **Its planning thread:** a link to `/planning/<short key>`, where the owner talks a card through and signs it off too.
- No planner box yet. ADR 19 item 5 comes later.

- The owner (2026-10-06): the board replaces the Milestones tab. With this page done, remove "Milestones" from the tabs in `factory_dashboard/templates/base.html` (the Board tab, from f5-16, is how milestones are found), and a milestone's page lights the Board tab. `/milestones` still answers, for old links.
  - The Milestones list is the only place with each card's ↑ and ↓ (f6-18) and the trend charts, so the board links to it ("All milestones and their trends ›") once its tab is gone.

### Done when
- the top bar has no Milestones tab, `/milestones` still answers 200, and `/board` links to it
- the header shows the stage, the priority and the area, asserted within the header
- the current stage is marked in "How it grew" and no later one is
- a set-aside ticket reads "set aside" in its row
- the page links to the card's planning thread
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
