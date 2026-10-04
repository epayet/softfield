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
- A queued job's row reads its kind in plain words ("Checkpoint", "Review", "Direction", "Escalation", "Planning"), its subject, and its reason; one waiting for a reset says until when.
- Tickets keep their rows as today.

### Done when
- with a queued checkpoint and two ready tickets, the checkpoint's row comes first and shows its reason, asserted within that row
- a row with `not_before` in the future says "waits until HH:MM"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
