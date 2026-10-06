---
id: f8-07-queue-view
milestone: f8-one-queue
depends_on: [f8-05-replan]
difficulty: 4
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/queue.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's queue lists every queued job, not only tickets, in the order the runner will take them, each with its kind and reason.

### Context
Read D1–D2 in `docs/milestones/f8-one-queue.md`, `queue` in `factory_dashboard/overview.py` (tickets only today), `factory_dashboard/templates/_partials/queue.html`, `runner/dispatch.py` (the order) and `tests/factory_dashboard/test_overview.py`.
- **The queued jobs** are the project's open `work_queue` rows: `open_jobs` in `runner/metrics.py`, each made a `Queued` with `Queued.from_row` (`runner/dispatch.py`).
- **Their order and wait:** `plan` in `runner/dispatch.py`, given those rows, no tickets and an empty `Windows()`. Each `Line` has the job (`kind`, `subject`, `reason`) and `waits`: "waits until Mon 5 Oct 17:00" for a `not_before` still ahead, else None. Show `waits` as it is.
- Leave out a row whose `started_job` is a job still running: Now shows it, as `queue` leaves out a ticket with a running job.
- A queued job's row reads its kind in plain words ("Checkpoint", "Review", "Direction", "Escalation", "Planning"), its subject, and its reason. They come before every ticket.
- Tickets keep their rows as today.

### Done when
- with a queued checkpoint and two ready tickets, the checkpoint's row comes first and shows its reason, asserted within that row
- a queued escalation comes before an older queued checkpoint
- a row with `not_before` in the future says "waits until" and that time; a done row isn't shown
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
