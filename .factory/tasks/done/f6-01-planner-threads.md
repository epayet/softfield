---
id: f6-01-planner-threads
milestone: f6-planning-room
depends_on: [f5-01-requests-apply, f5-04-cards, f8-03-support-jobs-queued]
agent: lead
difficulty: 7
files:
  - runner/metrics.py
  - runner/planner.py
  - runner/requests.py
  - runner/loop.py
  - runner/claude.py
  - workflow/runner.toml
tests:
  - tests/runner/test_planner.py
  - tests/runner/test_requests.py
  - tests/runner/test_loop.py
---

### Goal
The runner answers the owner's planning messages first: each card (and one general thread) has a conversation with the lead, continued turn by turn, stored for the dashboard.

### Context
Read `docs/adr/20-planning-room.md` (items 1–5), D1–D3 in `docs/milestones/f6-planning-room.md`, D1–D3 in `docs/milestones/f8-one-queue.md`, `runner/requests.py` and `runner/metrics.py` (F5's requests, `queue_job`), `runner/dispatch.py`, `runner/claude.py` (how `claude -p` runs, sessions, readings) and `runner/loop.py` (`run_queued`, `claude_hold`, `park_row`). Test-first.
- **Tables (D1):** `planner_threads` (card key or `general`, Claude session id) and `planner_messages` (thread, author, time, text, `points` JSON, `proposals` JSON, job id).
- **The request kind `plan_message`** carries: thread, free text, and comments per point number.
- **A queued row per message (ADR 22 item 1):** `apply_requests` takes a `plan_message` by queueing a `planner` row (`queue_job`, reason "your message on F7"), and finishes the request with "queued for the lead". Its subject names the thread and the request id (`f7#41`): one open row per kind and subject is the rule `enqueue` keeps, so two messages on a thread need two subjects. The message stays in its request row.
- **Planner jobs first:** `pick` already puts `planner` before every other kind, by age; nothing to change there. `run_queued` gets a `planner` branch:
  - run a `planner` job (role in `[roles]`: `claude-opus`) with `claude -p --resume <session>` (a new session for a new thread);
  - parse the reply's JSON block (D2);
  - record it; `run_queued` finishes the row.
  - A reply without a valid block is recorded as text, with a note.
- **The window:** a planner job may use the owner's 25% (ADR 20 item 2): `claude_hold` keeps it back unless the 5-hour switch is on, so the planner's check lets it use both reserves. At a hard limit its row parks (`park_row`), like other support jobs, and the message waits.
- Each reply raises an owner item `planning` (ADR 20 item 9), resolved when the owner sends their answers.

### Done when
- two `plan_message` requests on one thread make two open `planner` rows, each with its reason
- two queued messages and a ready lead ticket: the messages' planner jobs run first, the second resuming the first's session
- a reply's points and proposals are stored; a reply with a broken block is stored as text with a note
- at 80% of the 5-hour window a planner job still runs; a lead ticket parks
- `uv run runner check-all --task f6-01-planner-threads` passes

```yaml
# --- runner ---
result: done
agent: lead
attempts: 1
```
