---
id: f9-20-fix-queue-count-with-jobs
milestone: f9-line-polish
difficulty: 2
depends_on: []
files:
- factory_dashboard/templates/_partials/queue.html
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f9-line-polish-C2-2
---

### Goal
Fix a checkpoint finding on f8-11-fix-the-queue-can-claim: with queued jobs and no tickets, the queue's first line reads "0 tickets waiting. Drain it with None".

### Context
Found by the lead at a checkpoint, on the merge of `tasks/done/f8-11-fix-the-queue-can-claim.md`. Read `factory_dashboard/templates/_partials/queue.html` and `_live_context` and `_drain` in `factory_dashboard/overview.py`.
- f8-11 changed the condition to `queue or queued_jobs`, but the line inside still counts only tickets and prints `drain`. `_live_context` sets `drain` to `None` when there are no queued tickets, so with only a queued job the page says "0 tickets waiting. Drain it with `None`".
- Its test `test_queue_with_queued_jobs_says_how_many` (name says "how many") checks only that "The queue is empty." is absent and that "Checkpoint:" appears, so it passes on that line.

### Done when
- with no tickets and one queued job, the queue's first line names the jobs waiting by count in plain words, never says "0 tickets" and never shows `None`; with tickets it still says how many tickets wait and the drain command
- the test for it asserts the exact line (the count and the absence of "None" and "0 ticket") and would fail on main
- the listed `tests:` pass
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2156
gate_failures: []
tokens: 919151
```
