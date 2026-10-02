---
id: f5-01-requests-apply
milestone: f5-board
depends_on: [f4-09-later-folder]
agent: lead
difficulty: 6
files:
  - runner/metrics.py
  - runner/requests.py
  - runner/loop.py
  - runner/cli.py
tests:
  - tests/runner/test_requests.py
  - tests/runner/test_metrics.py
  - tests/runner/test_loop.py
---

### Goal
The runner carries out the owner's requests from the metrics database (sign off, the 5-hour answer, queue a ticket) exactly as their console commands would, at each pick, while it waits for an answer, and at the start of every command.

### Context
Read `docs/adr/18-dashboard-writes.md`, D1 and D2 in `docs/milestones/f5-board.md`, `runner/metrics.py` (`MIGRATIONS`, `upsert_owner_item`), `runner/owner.py` (`signoff`), `runner/loop.py` (`read_answer`, `_ask_five_hour`, `work_queue`) and `runner/cli.py`. Test-first.
- The `queue` kind calls the function behind `runner queue` (f4-09). The `five_hour` kind answers the 5-hour question: a waiting `_ask_five_hour` takes it as typed input, and with no question waiting it sets the same yes or no for the command (`FIVE_HOUR`).
- `read_answer` waits on stdin with `select`. Make it also return an open `five_hour` request, checking the database every 5 s, so a phone's answer lands within seconds.
- A request is finished once, with its `result` ("signed off f4-always-on", or the error).

### Done when
- a `signoff` request for a milestone with work left is finished with the same error `signoff` prints, and changes nothing
- a `queue` request moves the ticket and commits, like the command
- a `five_hour` yes while the runner waits on the question lets the ticket go within one poll
- requests made while nothing runs are applied by the next `runner` command
- `uv run runner check-all --task f5-01-requests-apply` passes
