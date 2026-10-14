---
id: f14-04-failed-edit-shows-on-desk
milestone: f14-coming-planted-ideas-not-clickable
difficulty: 5
depends_on: []
agent: lead
finding: f14-coming-planted-ideas-not-clickable-F1
files:
  - runner/requests.py
  - factory_dashboard/planning.py
  - factory_dashboard/templates/planning.html
tests:
  - tests/runner/test_requests.py
  - tests/factory_dashboard/test_planning.py
---

### Goal
An edit of a waiting plant or message that didn't go through (it came too late, or the runner refused its words) shows on the desk under "Didn't go through", with the owner's new words and the runner's reason, until they dismiss it.

### Context
Read `docs/milestones/f14-coming-planted-ideas-not-clickable.md` (Done when, last line) and `docs/reviews/f14-coming-planted-ideas-not-clickable.md` (F1). Today a `change` finished as "too late: already sent" shows nowhere: the thread is drawn again with the message stored and no status, and the new words stay in `owner_requests` only. A plant's shows in Coming only until the pick that finishes it. The owner's rule (`docs/agents/owner.md`, 2026-10-08): their words are never refused unseen.
- In `runner/requests.py`: `owners_words` gives None for a `change`, so `refused` and `_dismiss` never see one. `WORDS` is spread into two SQL `IN (?, ?, ?)` lists in `factory_dashboard/planning.py` (`_refused`, `_retried`): a fourth kind needs a fourth mark, or its own name.
- An edit's words are its value's: a plant's `{"title", "thoughts"}` or `{"text"}`, a message's `{"text", "comments"}`. A cancel (`{"cancel": true}`) carries no words and is never shown here: its result shows where it was asked.
- A change worked when its result is `CHANGED`; any other result of an edit is a refusal.
- The desk's row (`RefusedItem`, built in `_refused`, drawn in `factory_dashboard/templates/planning.html`): the title says what was edited ("Your edit of <the plant's title>", "Your edit on <the thread's title>": the change's `subject` is the target request's id), the reason is the runner's result, the words are the edit's.
- A message's edit offers Try again to its thread's reply box, as a refused message does (`_again` checks `_message_thread`, which reads a change's subject as a thread: it needs the target's). A plant's edit offers Dismiss only: the idea is a card by then, and planting the words again would make a second one.
- **A row that was never an edit (a cancel, a change finished as "changed") must not appear, and a dismissed one must leave at once, as the other refused rows do.**

### Done when
- an edit finished as "too late: already planted" or "too late: already sent" shows under "Didn't go through" with its new words and that reason
- an edit the runner refused for its words (a bad value) shows the same way
- a cancel, whatever its result, and an edit finished as "changed" show nothing there
- Dismiss on the row posts a `dismiss` naming the change; the runner accepts it and the row leaves the desk
- Try again on a message's edit opens its thread with the new words in the reply box; a plant's edit has no Try again
- `refused` and `owners_words` are unchanged for the three kinds they read today (the existing tests keep every assertion)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
