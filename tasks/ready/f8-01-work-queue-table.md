---
id: f8-01-work-queue-table
milestone: f8-one-queue
depends_on: []
agent: lead
difficulty: 3
files:
  - runner/metrics.py
tests:
  - tests/runner/test_metrics.py
---

### Goal
The metrics database has a `work_queue` table, and `runner/metrics.py` can queue a job, list the open ones and finish one.

### Context
Read `docs/adr/22-one-visible-queue.md` item 1, D1 in `docs/milestones/f8-one-queue.md`, and in `runner/metrics.py` the migrations `_V1`…`_V5` and `add_request`, `open_requests`, `finish_request` (the same shape for F5's requests). Test-first.

### Done when
- a fresh database and one at `_V5` both migrate to the table
- `open_jobs` returns the project's rows that aren't done, oldest first, with their `not_before`
- `uv run runner check-all --task f8-01-work-queue-table` passes
