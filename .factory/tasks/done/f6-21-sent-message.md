---
id: f6-21-sent-message
milestone: f6-planning-room
depends_on: []
difficulty: 3
files:
  - factory_dashboard/planning.py
  - factory_dashboard/templates/thread.html
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
On a thread, a message the owner sent shows at once as theirs, with a dashed orange edge and "waiting for the lead", and the Send box goes, instead of "Asked: the runner will do it" under a box they can still edit.

### Context
Read `thread_page` and `_messages` in `factory_dashboard/planning.py`, and `factory_dashboard/templates/thread.html`: the messages loop, the `#waiting` paragraph (shown while `next_reply` is set) and the `#reply` form, whose Send posts a `plan_message` and puts `factory_dashboard/templates/_partials/request.html`'s "Asked: the runner will do it" in `#reply-status`.
- Today the runner turns the request into a `planner_messages` row and a planner job only at its next pick, which can be most of an hour away. Until then the page knows nothing of the message.
- The owner (2026-10-07): "when i put a question on an existing ticket, it currently just says the runner will look and i can still edit the comment like nothing happened".
- In `thread_page`: the open `plan_message` requests for this thread (`owner_requests`, `kind = 'plan_message'`, `subject` the thread, `done IS NULL`), oldest first, become `Message`s from the owner after the stored ones, with their value's `text` and comments as points. Mark them sent but not yet picked up (a new `Message` field, `waiting: bool`, default False), and count them as pending, so `next_reply` is set and the form is replaced by `#waiting`.
- In the template, a waiting message has `border: 1px dashed var(--hazard)` and, under its text, "Sent · the runner picks it up at its next pick".
- On Send, the form's `hx-target` becomes the thread's messages and the Send box (one element around both, `#conversation`), re-fetched from the page with `hx-select`, so the message and `#waiting` show without a reload.

### Done when
- with an open `plan_message` request for the thread, the page shows its text as the owner's latest message with "Sent", shows `#waiting`, and has no `#reply` form; once the request is done and its `planner_messages` row exists, the text shows once, as an ordinary message
- a browser test: typing a message and pressing Send shows the message and `#waiting`, and the Send box is gone, without a reload
- assert within the message's element, on its text with tags stripped and entities unescaped (`_text` in `tests/factory_dashboard/test_planning.py`)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 7677
gate_failures: ['task-tests', 'protected-paths']
tokens: 7051976
```
