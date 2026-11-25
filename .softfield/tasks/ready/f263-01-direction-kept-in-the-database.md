---
id: f263-01-direction-kept-in-the-database
milestone: f263-on-the-console-run-you-can
difficulty: 3
depends_on: []
agent: lead
files:
  - runner/metrics.py
  - runner/developer_job.py
tests:
  - tests/runner/test_metrics.py
  - tests/runner/test_loop.py
---

### Goal
The lead's direction to a developer's last attempt is kept, whole, on the direction job's row in the metrics database, so the dashboard can show it (F263 D1).

### Context
- Read `.softfield/cards/f263-on-the-console-run-you-can.md`, D1.
- Today the text is read in `give_direction` (`runner/developer_job.py` since F290) from the direction file in the ticket's logs (`direction_file`) and only printed on the console (`call_claude`'s `↳` summary line); the job's `note` column holds its process note (what went wrong), not the direction.
- Add migration `_V17` in `runner/metrics.py` after `_V16`: `ALTER TABLE jobs ADD COLUMN direction TEXT;`, wired in like `_V16`. Add `set_job_direction(conn, job_id, text)`, following `set_job_model`.
- In `give_direction`, once `direction` is read and not empty, store it on the direction job's row: `call_claude` (in `runner/session.py` since F290) sets `s.last_job_id` to that job. A parked direction (``Parked`` raised) stores nothing; a run that resumes it stores it when it finishes. The ticket repair (`ticket_file`) is not stored.
- Nothing is backfilled.

### Done when
- a fresh database and an older one (at `_V16`) both end with `jobs.direction`
- after a direction that wrote its direction file, its job row's `direction` holds the file's whole text, stripped; the last-attempt job's row and every other row stay NULL
- a direction that wrote no direction file leaves the column NULL
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
