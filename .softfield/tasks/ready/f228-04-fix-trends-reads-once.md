---
id: f228-04-fix-trends-reads-once
milestone: f228-loading-the-overview-page-is-slow
difficulty: 3
depends_on: []
files:
- factory_dashboard/queries.py
tests:
- tests/factory_dashboard/test_queries.py
- tests/factory_dashboard/test_milestones.py
finding: f89-does-allowance-refresh-at-the-beginning-C1936-1
---

### Goal
Fix a checkpoint finding on f228-01-trends-reads-once: Lead tickets without lead jobs are dropped from the rate denominator

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f228-01-trends-reads-once.md`. What it found is under Finding:
- f89-does-allowance-refresh-at-the-beginning-C1936-1, should-fix: in `factory_dashboard/queries.py`, line 320.

### Finding
f89-does-allowance-refresh-at-the-beginning-C1936-1: Lead tickets without lead jobs are dropped from the rate denominator
> The merged ticket requires that “trends, savings and the Milestones page give the same numbers as before.” The inner join drops a lead ticket with no job, and the role filter also drops its lines when it has only non-lead jobs. Those lines should remain in the denominator while contributing no dollars or tokens, so omitting them can change the rates and savings.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
