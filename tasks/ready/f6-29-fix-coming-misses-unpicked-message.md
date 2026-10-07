---
id: f6-29-fix-coming-misses-unpicked-message
milestone: f6-planning-room
difficulty: 3
depends_on:
- f6-27-fix-coming-rows-lose-the
files:
- factory_dashboard/planning.py
tests:
- tests/factory_dashboard/test_planning.py
finding: f6-planning-room-C3-1
---

### Goal
Fix a checkpoint finding on f6-20-desk-coming: a thread whose message the runner has not picked up yet is not in Coming.

### Context
By the lead at a checkpoint, on the merge of `tasks/done/f6-20-desk-coming.md`. What it found is under Finding:
- f6-planning-room-C3-1, should-fix: in `factory_dashboard/planning.py`, `coming`, the thread query.

### Finding
f6-planning-room-C3-1: `coming` only lists threads whose latest stored `planner_messages` row is the owner's, so a thread with an open `plan_message` request and no row yet is missing.
> The runner turns a `plan_message` request into a `planner_messages` row only at its next pick, so right after Send the thread's last stored message is the lead's (or there is none) and the thread is skipped, although f6-20's Goal is exactly that gap ("i asked a question about test 1, and now it's gone?"). The check for an open request below the query never runs for it. Coming must list a thread with an open `plan_message` request (`owner_requests`, `done IS NULL`, `subject` the card) whatever its latest stored message, and one with an open planner row, once each. `thread_page` already reads such requests the same way.

### Done when
- with an open `plan_message` request for a thread whose last stored message is the lead's, Coming shows the thread with its link and "waiting for the lead"; once the request is done and the lead's reply is stored, it is not in Coming
- a thread with both an open request and an open planner row shows once
- what the finding describes no longer holds, and a test shows it, asserting within the Coming section on its text with tags stripped
- the listed `tests:` pass, and fail without the change
- all gates pass
