---
id: f6-25-fix-planning-links-use-an
milestone: f6-planning-room
difficulty: 3
depends_on: []
files:
- factory_dashboard/templates/_partials/queue.html
tests:
- tests/factory_dashboard/test_overview.py
finding: f6-planning-room-C529-1
---

### Goal
Fix a checkpoint finding on f6-15-queue-message: Planning links use an uppercase thread key and fail to load the thread.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f6-15-queue-message.md`. What it found is under Finding:
- f6-planning-room-C529-1, blocking: in `factory_dashboard/templates/_partials/queue.html`, line 16.

### Finding
f6-planning-room-C529-1: Planning links use an uppercase thread key and fail to load the thread.
> The link is rendered as `/planning/F11`, but the thread route queries `planner_threads.card` using the path value exactly, while card keys are lowercase. The ticket's Done when requires that “its link is `/planning/f11`”; use the lowercase thread key in the href.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1597
gate_failures: []
tokens: 290710
```
