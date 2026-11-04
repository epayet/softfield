---
id: f81-10-fix-now-readouts
milestone: f81-assess-the-current-ui-state-of
difficulty: 2
depends_on: []
files:
- factory_dashboard/templates/_partials/queue.html
tests:
- tests/factory_dashboard/test_app.py
- tests/factory_dashboard/test_overview.py
finding: f81-assess-the-current-ui-state-of-C1743-3
---

### Goal
Fix a checkpoint finding on f81-06-now-readouts: Queued-job count has no text separator

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-06-now-readouts.md`. What it found is under Finding:
- f81-assess-the-current-ui-state-of-C1743-3, should-fix: in `factory_dashboard/templates/_partials/queue.html`, line 7.

### Finding
f81-assess-the-current-ui-state-of-C1743-3: Queued-job count has no text separator
> The ticket's Goal says the “Queue's count is one big number.” In the queued-jobs branch the number directly touches the `<small>` text, producing text such as `1job waiting.`; the CSS margin only separates it visually. Include a whitespace separator as in the tickets branch.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
