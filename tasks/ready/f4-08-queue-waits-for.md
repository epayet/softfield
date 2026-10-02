---
id: f4-08-queue-waits-for
milestone: f4-always-on
depends_on: []
difficulty: 4
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
The Overview's Queue lists the waiting tickets in the order the runner will take them, leaves out the ticket being worked on, and says what each blocked one waits for.

### Context
Read `factory_dashboard/overview.py` (`Queued`, `queue`, `live_runs`), the `queue` section of `factory_dashboard/templates/overview.html`, `runner/tasks.py` (`pick_next`, `blocked_ids`) and the queue tests in `tests/factory_dashboard/test_overview.py`.
- Facts: `queue` takes every `tickets` row with `state = 'ready'` and sorts by milestone then id. A ticket being worked on can still show, and a ticket waiting on another looks the same as one ready now.
- **The rules (`docs/milestones/f4-always-on.md` D3):**
  - Leave out any ticket that has a job with `outcome = 'running'`.
  - `tickets.depends_on` is a JSON list of ticket ids. A ready ticket whose dependencies are all `done` is "ready now". Otherwise it "waits for <id>", naming the first one not done, or "waits for <id>'s escalation" when that one's state is `escalated`.
  - A ready ticket with `kind = 'lead'` while a live run's `activity` starts with "waiting for Claude" "waits for Claude".
  - Order: the ready-now ones first, by milestone order then id (as `pick_next` does), then the waiting ones in the same order.
- Show the reason in a "Waits for" column, empty for "ready now".
- Put your new fixture rows in your own function in `tests/factory_dashboard/conftest.py`.

### Done when
- a ticket with a running job isn't in the Queue
- a ticket whose dependency is ready, not done, reads "waits for <that id>" in its row; one whose dependency is escalated reads "waits for <that id>'s escalation"
- a lead ticket reads "waits for Claude" while a live run's activity is "waiting for Claude · …"
- ready-now tickets come before waiting ones
- each assertion reads its own row
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
