---
id: f279-06-fix-next-in-line-from
milestone: f279-i-would-like-to-be-able
difficulty: 3
depends_on: []
files:
- factory_dashboard/templates/_partials/queue.html
tests:
- tests/factory_dashboard/test_overview.py
finding: f279-i-would-like-to-be-able-C2757-1
---

### Goal
Fix a checkpoint finding on f279-04-next-in-line-from-the-plan: Whole-queue link has extra counts instead of required link text

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f279-04-next-in-line-from-the-plan.md`. What it found is under Finding:
- f279-i-would-like-to-be-able-C2757-1, should-fix: in `factory_dashboard/templates/_partials/queue.html`, line 21.

### Finding
f279-i-would-like-to-be-able-C2757-1: Whole-queue link has extra counts instead of required link text
> The Done when says "The whole queue ›" opens `/queue`, but the merged template renders `The whole queue: {{ plan.tickets }} tickets, {{ plan.job_count }} jobs ›`, replacing the ticket's required label and potentially failing content assertions.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1088
gate_failures: []
tokens: 749014
```
