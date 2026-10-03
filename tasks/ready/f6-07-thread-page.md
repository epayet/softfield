---
id: f6-07-thread-page
milestone: f6-planning-room
depends_on: [f6-06-desk-page]
difficulty: 6
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card's thread page shows the conversation, the lead's points with everything agreed by default and a Comment… box on each, a free message, and the card's proposals; sending posts the owner's answers in one request.

### Context
Read the mock-up (`docs/milestones/planning-room-mockup/Main.dc.html`, `docs/milestones/planning-room-mockup/Review.dc.html`, `docs/milestones/planning-room-mockup/Phone.dc.html`: read the markup and the data in each script, not pages to open) (`docs/milestones/planning-room-mockup/Main.dc.html`: the thread and the proposals column; ignore its Agree buttons: agreed is the default, owner 2026-10-03), D1–D3 in `docs/milestones/f6-planning-room.md`, `factory_dashboard/planning.py` (f6-06) and `factory_dashboard/requests.py`.
- **`/planning/<thread>`:**
  - the card's header;
  - each message in order: the owner's text, the lead's text, then its numbered points (title, answer, "→ action"), each with a "Comment…" toggle opening a textarea;
  - a progress line ("7 points · 1 comment");
  - the free message box;
  - "Send": one `plan_message` request with the free text and the comments by point number.
- **The proposals column:** each proposal's kind, title and state, linking to its review page (f6-08).
- **While a reply is pending:** "Next for the lead · ~N min" and no Send button.

### Done when
- a fixture reply with 7 points shows each point's title, answer and action, asserted within the point
- a Send with comments on points 2 and 4 posts one request carrying them and the free text
- a pending reply hides Send and shows the wait
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
