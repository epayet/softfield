---
id: f171-01-tickets-join-their-card
milestone: f171-there-are-dupliacted-tickets-on-the
agent: lead
difficulty: 5
priority: 3
depends_on: []
files:
  - runner/loop.py
  - runner/metrics.py
  - runner/tasks.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_metrics.py
---

### Goal
A ticket whose frontmatter names its card by the short key (`milestone: f4`) is filed under the card's own row, with its jobs and findings, and the empty short-key rows already in the database are folded into their cards.

### Context
Read D1 and D2 in `.softfield/cards/f171-there-are-dupliacted-tickets-on-the.md`, then `record_ticket` and `start_job` in `runner/loop.py`, `full_key` in `runner/tasks.py`, `_Backfill.key` in `runner/backfill.py` (it already resolves a short key this way), and `upsert_milestone` in `runner/metrics.py`.
- The case on the owner's machine: travel-companion's `f4-0*` tickets say `milestone: f4` while its card's doc is f4-after-my-message-i-have-the.md, and the database holds an untitled row `f4` with those four tickets beside the card's row; `f2` likewise, with `f2-01-readme` (done) and one job.
- Resolve once, where the runner reads a ticket's milestone, so that every row it writes from that ticket (its row, its job's milestone, a checkpoint's findings on it) uses the full key. Don't change what pre-flight accepts.
- The fold (D2) runs on every sync, so it repairs the rows already there and any one a later short key makes. It moves only a row with no title, state, status or sign-off of its own, into the project's non-removed row with the same short key; with none (F107's, whose cards were merged away), the row stays.

### Done when
- a ticket with `milestone: f4`, when `.softfield/cards/f4-some-card.md` exists, is recorded under `f4-some-card`, and a job on it too; no row `f4` is made
- with no doc for `f4`, the ticket is recorded under `f4`, as today
- an empty row `f4` holding tickets and a job is folded into `f4-some-card` at the next sync: they move, the empty row goes
- a row `f4` with a title, state or status of its own, or with no non-removed `f4-…` row, is left as it is
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
