---
id: f6-15-queue-message
milestone: f6-planning-room
depends_on: []
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
On the Overview's Next in line, a planning row shows what the owner asked: the start of their message, and the whole of it on hover, as a link to its thread. A plant the runner hasn't done yet is a row too.

### Context
Read `QueuedJob` and `queued_jobs` in `factory_dashboard/overview.py` and the `queued_jobs` loop in `factory_dashboard/templates/_partials/queue.html` (today `Planning: f11#3 · your message on F11`). Follow the ticket rows just below it in the same template: a link in `<b class="mono">`, then words after `·`.
- A planner row's subject is `<thread>#<request id>` (`row_subject` and `request_of` in `runner/planner.py`). The request is the `owner_requests` row with that id; its `value` is JSON `{"text": …, "comments": {"2": …}}`. When `text` is empty, use the first comment.
- The row reads: `Planning: <a href="/planning/f11">F11</a> · “this is a test, say hi”`. Cut the text at 60 characters with "…" after it, and put the whole text in the row's `title` attribute.
- A pending plant: an `owner_requests` row with `kind = 'plant'` and `done IS NULL`; its `value` is JSON `{"title", "thoughts"}`. It shows after the planning rows as `Plant: <title> · at the runner's next pick`, with no link (its card doesn't exist yet).
- The owner (2026-10-07): "it'd be good to see the message, but shouldn't be too long, perhaps some hover state… or seeing at the least the beginning of the message and then… and it would be good to link to the thing to see the whole chat history"; "whenever i plant something, it should show on the overview queue".

### Done when
- with a planner row for a 100-character message, the row's text holds its first 60 characters and "…", its `title` holds all 100, and its link is `/planning/f11`; a message with no text shows its first comment
- an open `plant` request shows a `Plant: <title>` row; a done one shows none
- assert on the row's text with tags stripped and entities unescaped, within that row (`_text` in `tests/factory_dashboard/test_planning.py` is the example to follow)
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 3
duration_s: 7289
gate_failures: ['ruff', 'task-tests']
tokens: 5951510
```
