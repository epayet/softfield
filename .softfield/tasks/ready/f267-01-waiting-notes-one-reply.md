---
id: f267-01-waiting-notes-one-reply
milestone: f267-being-able-to-comment-on-a
difficulty: 4
depends_on: []
files:
  - runner/loop.py
  - runner/planner.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_planner.py
agent: lead
area: factory
---

## Goal
One planner job answers every owner message waiting on its thread, so notes the owner adds while the lead writes get one reply, not one each.

## Context
- Read `.softfield/cards/f267-being-able-to-comment-on-a.md`, D2 and D3.
- `run_planner` in `runner/loop.py` answers one queued row (`row.subject` is `<thread>#<request id>`, `planner.request_of`); `planner.look_of` tells a runner's look at a blocked ticket, which never joins.
- The thread's open rows: `metrics.open_jobs` (kind `planner`, `started_job` empty when not started); close the joined ones with `metrics.finish_queued`, as the job's own row is closed.
- The prompt: `prompt` in `runner/planner.py` takes one text and its comments today; give it the messages in the order sent, each with its comments, and keep a single message's prompt as it is now.

## Done when
- Three owner messages queued on one thread: one job runs, its prompt holds all three in order with each one's comments, all three rows are closed, and the thread gets one lead message.
- A runner's blocked-ticket row on the same thread, and rows on other threads, stay queued.
- A row already started, or held for a Claude limit, isn't joined.
- With one message waiting, the prompt is unchanged.
- A failed job leaves one lead message saying to send again, and closes the joined rows as its own.
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
