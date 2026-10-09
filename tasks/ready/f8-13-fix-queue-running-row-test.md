---
id: f8-13-fix-queue-running-row-test
milestone: f8-one-queue
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f8-one-queue-F3
tests_only: true
---

### Goal
Fix a review finding on f8-07-queue-view's tests: no test shows that a queued job whose job is running is left out of the queue.

### Context
The code is right and its test is missing: change only tests. They pass on main's code, as they should.
- `queued_jobs` in `factory_dashboard/overview.py` leaves out an open `work_queue` row whose `started_job` is a job with `outcome = 'running'`: Now shows that job, so the queue mustn't list it twice (`tasks/done/f8-07-queue-view.md`, its Context).
- Follow `test_queued_checkpoint_comes_before_tickets_and_shows_reason` in `tests/factory_dashboard/test_overview.py`: it queues a row with `metrics.queue_job` and reads the queue from `/live` with `section(html, "queue")`.
- To give a row its job, take the id of a job the `client` fixture's database has with `outcome = 'running'` and set the row's `started_job` to it with an `UPDATE work_queue`; for the other case, a job whose outcome is `passed`.

### Done when
- a queued checkpoint whose `started_job` is a running job is not in the queue section of `/live` (its reason is absent)
- the same row whose `started_job` is a finished job is listed, with its reason
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
