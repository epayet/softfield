---
id: f211-03-open-plan-on-thread-page
milestone: f211-a-plan-must-not-get-lost
difficulty: 5
depends_on: [f211-02-keep-plan-as-new-card]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/thread.py
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/thread.html
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/templates/_partials/open_plan.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
  - tests/factory_dashboard/test_milestones.py
---

### Goal
Sign off warns when a plan is still open on the card and offers "Keep it as a new card"; Archive stays as it is, naming the plan it closes.

### Context
The picture to build is `.softfield/cards/f211-mockup/open-plan.html`, pictures 1 to 4. Read `.softfield/cards/f211-a-plan-must-not-get-lost.md`: D3, D4 and D7.
- `factory_dashboard/planning.py`: add `open_plan` here (`milestones.py` already imports from this file). `_put_aside` is the worked example of reading a thread's latest list with `proposal_state`.
- `factory_dashboard/thread.py`: `thread_page` builds the page's values, `_review` says whether the card is ripe and `pending` whether a message waits. `factory_dashboard/milestones.py` calls `_review` for the same Sign off.
- `factory_dashboard/templates/thread.html`: `#review` holds Sign off and `#archive` holds Archive. `factory_dashboard/templates/milestone.html`: `#review` holds the other Sign off. Both use the shared partial.
- A press shows at once, dashed, as `#signing-off-shape` does: "Keeping as a new card at the runner's next pick", also after a reload while the `keep_plan` request is open. The runner's refusal shows beside the button, as `review.refused` does.
- A `keep_plan` request posts the thread's short key as its subject (`factory_dashboard/requests.py`).

### Done when
- a ripe card with an open plan: `#review` shows the plate with the plan's title linked to its proposal page, Keep as the yellow button and Sign off plain, and Sign off still works with one press
- a ripe card whose owner's message still waits for the lead: a line says so, with or without an open plan
- the same plate and buttons on the card's milestone page
- an unarchived thread with an open plan: the Archive button as today, plain and one press, with one line beside it naming the plan and saying it won't be built unless the owner replies
- the same on a done card, with a plain Keep beside Archive; on any other card no Keep by Archive
- a thread already archived: no line and no Keep, and Unarchive as today
- a card with no open plan, or only an open seed or merge: both pages as they are today
- Keep pressed: the dashed line at once and after a reload; no button left to press again
- on a 390 px phone every button is at least 44 px tall and nothing overflows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
