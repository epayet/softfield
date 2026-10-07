---
id: f14-03-edit-waiting-message
milestone: f14-coming-planted-ideas-not-clickable
difficulty: 4
depends_on: [f14-01-change-request, f14-02-coming-editor]
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A message the owner sent on a thread, still waiting for the runner's pick, has Edit and Cancel it.

### Context
Read `docs/milestones/f14-coming-planted-ideas-not-clickable.md` (Done when, D5) and `thread_page` in `factory_dashboard/planning.py`: open `plan_message` requests become `Message`s with `waiting=True`, shown in `factory_dashboard/templates/thread.html`. Follow the desk's editor from f14-02 for the look and the posts.
- A change is a `change` request: `subject` the message's request id, `value` `{"text", "comments"}` or `{"cancel": true}` (f14-01).
- **Only a message with `waiting=True` gets the buttons; a message the runner has taken is on the thread for good.**

### Done when
- a waiting message shows Edit and Cancel it; a stored one shows neither
- Edit opens its text in place with Save; Save posts a `change`, and the message shows the new text at once, on its way, without the buttons
- Cancel it posts a `change` with `{"cancel": true}`; the message shows struck through, "cancelling at the runner's next pick", without the buttons
- with every waiting message on the thread cancelled, the Send form comes back (nothing is waiting for the lead)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
