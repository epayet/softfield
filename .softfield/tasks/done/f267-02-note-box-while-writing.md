---
id: f267-02-note-box-while-writing
milestone: f267-being-able-to-comment-on-a
difficulty: 2
depends_on: []
files:
  - factory_dashboard/templates/thread.html
  - factory_dashboard/static/dashboard.css
tests:
  - tests/factory_dashboard/test_thread.py
area: factory
---

## Goal
A thread's message box stays on the page while the lead owes a reply, so the owner can add notes then.

## Context
- The picture to build: `.softfield/cards/f267-mockup/note-while-writing.html` (Proposed).
- Read `.softfield/cards/f267-being-able-to-comment-on-a.md`, D1.
- `factory_dashboard/templates/thread.html`: `#reply` is drawn only `if not next_reply`; the point comment boxes (`comment-box`) have their own `next_reply is none` rule, which stays.
- A note sent then is a waiting message, drawn as F14's already are (dashed, Edit, Cancel it): follow the existing tests for waiting messages in `tests/factory_dashboard/test_thread.py`.

## Done when
- With the lead writing a reply on the thread, or a message of the owner's waiting, the page has the box labelled "Add a note · the lead reads it after this reply", a button "Add note" and the aside "Every note sent before the lead starts again goes in one reply.", under a plate as in the mock-up (hazard stripe, "Add a note", "after this reply", corner ticks; `.aside .plate` in `factory_dashboard/static/dashboard.css` is the example)
- While the lead is writing this thread's reply (`writing_now`), a waiting message's line reads "Sent · the lead reads it after this reply" instead of "Sent · the runner picks it up at its next pick"; Edit and Cancel it stay.
- With nothing waiting, the box reads as today ("Anything else? A question, a new thought", "Send").
- A thread merged into one other card still has no box.
- While a reply is owed, the points still have no comment boxes.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: stopped)
attempts: 3
tokens: 3002905
logs: .softfield/var/runs/20261118-135500/f267-02-note-box-while-writing
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
