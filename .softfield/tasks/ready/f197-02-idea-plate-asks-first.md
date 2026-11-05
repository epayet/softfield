---
id: f197-02-idea-plate-asks-first
milestone: f197-reverse-plant-and-plant-and-ask
difficulty: 1
depends_on: [f164-03-idea-plates-with-plant]
files:
  - factory_dashboard/templates/_partials/idea.html
  - tests/factory_dashboard/test_thread.py
tests:
  - tests/factory_dashboard/test_thread.py
---

### Goal
On a review's idea plate, "Plant and ask the lead" comes first in yellow and "Plant" comes second as the plain button, as in the Plant box.

### Context
The picture to build is Proposed's idea plate in `.softfield/cards/f197-mockup/plant-buttons.html`. Read `.softfield/cards/f197-reverse-plant-and-plant-and-ask.md` (D1).
- F164's mock-up drew the plate the old way, and f164-03 built it from that picture. Its buttons are in `factory_dashboard/templates/_partials/idea.html`, which the card's thread and its milestone page both draw.
- Use the dashboard's own `btn go` and `btn plain` classes, as the Plant box in `factory_dashboard/templates/planning.html` does, and keep what each button posts.

### Done when
- on an idea with no plant, Plant and ask the lead comes before Plant in the page
- Plant and ask the lead carries `btn go` and Plant carries `btn plain`
- Plant and ask the lead still posts `ask` true and Plant `ask` false
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
