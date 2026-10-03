---
id: f6-08-proposal-review
milestone: f6-planning-room
depends_on: [f6-06-desk-page]
difficulty: 5
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/proposal.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A proposal's review page lays out its key points in plain words, agreed by default, with Comment… on each, and gives "Send back", "Accept ADR" or "Approve plan".

### Context
Read the mock-up (`docs/milestones/planning-room-mockup/Main.dc.html`, `docs/milestones/planning-room-mockup/Review.dc.html`, `docs/milestones/planning-room-mockup/Phone.dc.html`: read the markup and the data in each script, not pages to open) (`docs/milestones/planning-room-mockup/Review.dc.html`; agreed is the default), D1 and D4 in `docs/milestones/f6-planning-room.md`, `factory_dashboard/planning.py` and `factory_dashboard/requests.py`.
- **`/planning/<thread>/proposals/<id>`:**
  - tabs per proposal of the card (ADR, mock-up, plan);
  - the key points grouped as the proposal lists them, each with its ⚑ note;
  - a side panel with what happens next.
- **A mock-up proposal** shows its HTML file in a sandboxed `<iframe>` from `/planning/mockups/<path>`: a read-only route serving only files under `docs/milestones/*-mockup/`.
- **The buttons:**
  - with any comment, "Send back" posts `send_back`;
  - with none, "Accept ADR" posts `accept_adr`, and "Approve plan" posts `approve_plan`. "Approve plan" stays disabled while the card's ADR is still Proposed.

### Done when
- an ADR proposal's points show grouped, with their flags; a comment turns the primary button into Send back
- Approve plan is disabled while the card's ADR is Proposed, and enabled after
- the mock-up route serves a file under a `-mockup/` folder and refuses any other path
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
