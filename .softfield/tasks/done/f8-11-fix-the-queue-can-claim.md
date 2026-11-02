---
id: f8-11-fix-the-queue-can-claim
milestone: f8-one-queue
difficulty: 4
depends_on: []
files:
- factory_dashboard/templates/_partials/queue.html
tests:
- tests/factory_dashboard/test_overview.py
finding: f9-line-polish-C467-1
---

### Goal
Fix a checkpoint finding on f8-07-queue-view: The queue can claim it is empty while queued jobs are listed below.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f8-07-queue-view.md`. What it found is under Finding:
- f9-line-polish-C467-1, should-fix: in `factory_dashboard/templates/_partials/queue.html`, line 3.

### Finding
f9-line-polish-C467-1: The queue can claim it is empty while queued jobs are listed below.
> The empty-state condition checks only `queue` (tickets), ignoring `queued_jobs`. With no tickets but an open support job, the page says “The queue is empty” while showing that job. This breaks the ticket Goal: “The Overview's queue lists every queued job, not only tickets, in the order the runner will take them, each with its kind and reason.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1685
gate_failures: []
tokens: 1043833
```
