---
id: f6-06-desk-page
milestone: f6-planning-room
depends_on: [f6-05-replan, f5-02-requests-route, f5-14-factory-look]
difficulty: 5
files:
  - factory_dashboard/planning.py
  - factory_dashboard/app.py
  - factory_dashboard/templates/planning.html
  - factory_dashboard/templates/base.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
`/planning` is the owner's desk: what the factory does now and when the next reply comes, the lead's window, everything waiting for the owner, and "Plant an idea".

### Context
Read the mock-up (`docs/milestones/planning-room-mockup/Main.dc.html`, `docs/milestones/planning-room-mockup/Review.dc.html`, `docs/milestones/planning-room-mockup/Phone.dc.html`: read the markup and the data in each script, not pages to open) (`docs/milestones/planning-room-mockup/Main.dc.html`: the tiles and the left column), D1–D6 in `docs/milestones/f6-planning-room.md`, `factory_dashboard/requests.py` and its worked example in `docs/agents/developer.md`, and `factory_dashboard/overview.py` (live data, the allowance).
- **Two tiles:**
  - **"The factory now":** the running job, and when the next reply is expected ("after f4-04, ~6 min", from the running job's elapsed time and the queue). Planning is merged into this tile (owner, 2026-10-03).
  - **The lead's window:** the 5-hour meter with the 75% line, saying planning may go past it.
- **The desk:** groups, in this order:
  - your answers wanted (threads with a reply you haven't answered);
  - proposals to review;
  - finished cards to talk through (ripe);
  - seeds nobody has asked about.

  Each item links to its thread or proposal.
- **"Plant an idea":** title and thoughts, posting a `plant` request the way the worked example does.

### Done when
- with a fixture reply unanswered, a proposal and a ripe card, each shows in its group, in order, asserted within the group
- the factory tile names the running ticket
- the plant form posts a `plant` request with the title and thoughts
- the layout check passes at phone and desktop sizes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
