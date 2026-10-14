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
Read `docs/milestones/f14-coming-planted-ideas-not-clickable.md` (Done when, D5) and `thread_page` in `factory_dashboard/planning.py`: open `plan_message` requests become `Message`s with `waiting=True`, shown in `factory_dashboard/templates/thread.html`. Follow the desk's editor from f14-02 for the look and the posts: `factory_dashboard/templates/planning.html` lines 69–114 (a row with a change on its way, then the `<details class="waiting-plant">` editor with Save and Cancel it), and its tests at the end of `tests/factory_dashboard/test_planning.py` (from "a waiting plant is edited or cancelled from Coming").
- A change is a `change` request: `subject` the message's request id as text, `value` `{"text", "comments"}` or `{"cancel": true}` (f14-01).
- `open_changes(conn, project_id)` in `factory_dashboard/overview.py` gives the open changes by the id of the request each names: `.id` (the change's own request), `.cancel`, and `.title`, which is read as a plant's words. It holds no message text: an edit's new text is in the change's `value`, read with `message(...)` as `thread_page` reads a waiting message's.
- `Message` has no request id yet; the buttons' `subject` needs the `plan_message` request's `id`.
- The desk draws its row again after the post from the script at the bottom of `factory_dashboard/templates/planning.html` (the `.waiting-plant` lines). `factory_dashboard/templates/thread.html` has its own listener, bound to `#reply`; what it does for `#reply` stays, and no existing test loses an assertion.
- **Only a message with `waiting=True` gets the buttons; a message the runner has taken is on the thread for good.**

### Done when
- a waiting message shows Edit and Cancel it; a stored one shows neither
- Edit opens its text in place with Save; Save posts a `change`, and the message shows the new text at once, on its way, without the buttons
- Cancel it posts a `change` with `{"cancel": true}`; the message shows struck through, "cancelling at the runner's next pick", without the buttons
- with every waiting message on the thread cancelled, the Send form comes back (nothing is waiting for the lead)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: task-tests)
attempts: 3
tokens: 11350598
logs: var/runs/20261014-005521/f14-03-edit-waiting-message
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
