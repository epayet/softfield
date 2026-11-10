---
id: f211-05-work-on-another-card
milestone: f211-a-plan-must-not-get-lost
difficulty: 3
depends_on: [f211-03-open-plan-on-thread-page]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/thread.py
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/milestone.html
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
A card's review says when work approved on its thread sits on another card and isn't done yet, so a sign-off never leaves the owner wondering.

### Context
The picture to build is `.softfield/cards/f211-mockup/open-plan.html`, picture 6. Read `.softfield/cards/f211-a-plan-must-not-get-lost.md`: "What happened" (F149) and D12.
- `factory_dashboard/planning.py`: add `work_elsewhere` beside f211-03's `open_plan`. A worked `approve_plan` request has the subject of the thread and a `result` like "approved plan/f149: queued f164-07-review-fixes-are-quoted-too", which may list several tickets, comma-separated. `short_key` and the `tickets` table's `state` say whose a ticket is and whether it is done.
- `factory_dashboard/thread.py`: `_review` builds what `#review` shows. `factory_dashboard/milestones.py` calls it for the milestone page.
- A ticket links to `/tickets/<id>`, a card to `/planning/<short key>`.

### Done when
- a card whose approved plan queued another card's ticket, not done: one line in `#review` on the thread page reads "Also asked for here, still to come: <ticket>, on <card and title>. Signing off doesn't touch it.", with both links, before and after the sign-off
- the same line by Sign off on the milestone page
- several such tickets are all named
- once the ticket is done, the line goes
- a ticket of the card's own, a bug ticket (`bug-…`, which has no card), or an approval that was refused, makes no line
- Sign off stays as it is: same colour, same press, no plate
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
