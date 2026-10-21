---
id: f132-01-bar-follows-the-job
milestone: f132-the-overview-shows-the-whole-factory
difficulty: 3
priority: 2
depends_on: []
files:
  - factory_dashboard/app.py
  - docs/backlog.md
tests:
  - tests/factory_dashboard/test_app.py
---

### Goal
The top bar names the job that runs, whichever project it is in, never a project that only waits its turn between jobs.

### Context
Read `.factory/cards/f132-the-overview-shows-the-whole-factory.md` ("What happens today", D1), then `factory_wide_status` and `factory_status` in `factory_dashboard/app.py`. Follow the tests of `factory_wide_status` in `tests/factory_dashboard/test_app.py` (search for it): they seed several projects' runs and jobs.
- One runner serves every project, and each project keeps its own live run: a project waiting its turn says "picking the next ticket" (`PICKING`) for as long as another project's job runs.
- `factory_status` already returns the dot: `lead` or `developer` when a live job runs, `idle` for the between-jobs words.
- The rank becomes: a pause, or a pause or resume asked (as today); then a status whose dot is `lead` or `developer`; then "Waiting for Claude…"; then any other "Running: …"; then "Idle: …"; then Stopped. Equal ranks keep the owner's project order, as today.
- In `docs/backlog.md`, remove the f17-review line about "picking the next ticket" ranking with a running job: this ticket does it.

### Done when
- travel-companion first in the order, its run "picking the next ticket" with 9 ready tickets, and softfield running a developer job on f15-10-fix-wait-note-assertions-check: the bar says "Running: softfield · f15-10-fix-wait-note-assertions-check" with the developer's dot, on a page for any of the three projects
- the same with a planner job on softfield: "Running: softfield · planner, job 1097" with the lead's dot
- two projects between jobs and none running a job: the first in the order is named, as today
- a pause still comes before a running job; "Waiting for Claude until …" comes before a between-jobs line
- one project only: the words name no project, as today
- the backlog line is gone
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: all-tests)
attempts: 3
tokens: 6710315
logs: .factory/var/runs/20261021-090717/f132-01-bar-follows-the-job
```
