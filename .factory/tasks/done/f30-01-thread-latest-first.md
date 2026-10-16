---
id: f30-01-thread-latest-first
milestone: f30-on-conversations-i-want-to-the
difficulty: 3
depends_on: [f12-03-remove-review-probe]
files:
  - factory_dashboard/templates/thread.html
  - factory_dashboard/planning.py
tests:
  - tests/factory_dashboard/test_planning.py
---

### Goal
A card's thread page shows the latest exchange first, with Send right under the lead's latest answer, and folds the older messages under "Earlier in this thread (N)", newest first.

### Context
Read `factory_dashboard/templates/thread.html` (`#conversation`) and `thread_page` in `factory_dashboard/planning.py`: `messages` is built oldest first, with the owner's waiting messages (open `plan_message` requests) appended last; `Message.latest` marks the lead's latest message with points.
- The owner (2026-10-07): "on conversations, i want the latest answer first so that i don't have to scroll".
- Inside `#conversation`, top to bottom (`.factory/cards/f30-on-conversations-i-want-to-the.md` D1):
  1. when something waits: `#waiting` ("Next for the lead · …") and the owner's messages after the lead's latest message, newest first;
  2. the lead's latest message, with its points and Comment… as today;
  3. the `#reply` form, when nothing waits;
  4. a closed `<details id="earlier">` with the summary "Earlier in this thread (N)", holding every older message, newest first. No older message, no `#earlier`.
- With no lead message yet, every message shows open, newest first.
- Split the list in `thread_page` (latest group, earlier), not in Jinja; keep one `{% macro %}` (or include) for drawing a message, used by both parts.
- Keep `#reply` and its script inside `#conversation`: the re-fetch after Send (f6-21) must still redraw it all.
- Nothing else changes: same text, same styles.

### Done when
- a thread with three exchanges: the lead's latest message comes before `#reply`, and `#reply` before `#earlier`; `#earlier` is closed, says "Earlier in this thread (4)" and lists its messages newest first
- a waiting owner message shows above the lead's latest message, dashed, with `#waiting` and no `#reply`
- a thread with only one lead message has no `#earlier`; a thread with only the owner's first message (waiting) shows it and no `#earlier`
- the browser test of Send: the sent message appears at the top of `#conversation` without a reload
- the existing thread tests still pass, their order assertions updated
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 7761683
logs: .factory/var/runs/20261016-044031/f30-01-thread-latest-first
```
