---
id: f5-17-card-page
milestone: f5-board
depends_on: [f5-14-factory-look, f5-15-board-data]
difficulty: 4
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
tests:
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A milestone's page becomes its card's page: its stage, priority and area at the top, how far it has grown, and its tickets in run order with who works on each and which are set aside.

### Context
Read `docs/milestones/f5-board-mockup/Card.dc.html` (the picture: read its markup and the data in its script), `factory_dashboard/milestones.py` (the `/milestones/{key}` route), `factory_dashboard/templates/milestone.html`, `factory_dashboard/board.py` (the stages, f5-15) and `tests/factory_dashboard/test_milestones.py`.
- **The header:** the stage's icon and name, the priority, the area, and tickets done of total. Keep what the page shows today below it (the sign-off sheet, numbers, the Sign off button from f5-08).
- **"How it grew":** the six stages in a row, the card's own one lit and the later ones dimmed. Show dates only where the database has them: `milestones.started` on growing, `milestones.ended` on harvested.
- **The tickets:** in the runner's order (priority, then id), each with its goal, who did or will do it (the last job's agent, else "the lead" or "a developer" from its kind) and its state. Set-aside ones read "set aside".
- No planner box yet. ADR 19 item 5 comes later.

### Done when
- the header shows the stage, the priority and the area, asserted within the header
- the current stage is marked in "How it grew" and no later one is
- a set-aside ticket reads "set aside" in its row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
