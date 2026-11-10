---
id: f191-06-repair-doesn-t-wait-for-a-limit
milestone: f191-why-is-the-lead-reviewing-something
agent: lead
difficulty: 4
depends_on: [f191-05-fix-ticket-holds-only-its-review]
files:
  - runner/loop.py
  - tests/runner/test_loop.py
tests:
  - tests/runner/test_loop.py
---

### Goal
The one-turn repair of a ticket that fails pre-flight no longer waits for Claude: refused by a certain limit or stopped by an expired login, it gives up as a failed repair does.

### Context
Read cause 5 and D6 in `.softfield/cards/f191-why-is-the-lead-reviewing-something.md`.
In `runner/loop.py`: `_repair_ticket` calls `call_claude` with no `park`, and returns the problems left; `_repair_requeue` and the checkpoint's call already act on a list of problems. `_park` must not run for this turn: the job that wrote the ticket has ended, so there is nothing to resume.
Find the existing tests with a search for `_repair_ticket` and "fails pre-flight" in `tests/runner/test_loop.py`.

### Done when
- A repair refused by a certain limit returns the ticket's problems at once, with no wait, and the run goes on as after a repair that didn't help.
- The same for a repair stopped by an expired login; the owner's login item still shows.
- The refusal is still recorded as a usage event, so Claude counts as limited for the next job.
- A repair that isn't refused works as today.
- A repair given up leaves nothing in `state.interrupted` or `state.in_flight`.
