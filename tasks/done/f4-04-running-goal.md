---
id: f4-04-running-goal
milestone: f4-always-on
depends_on: []
difficulty: 3
files:
  - factory_dashboard/overview.py
  - factory_dashboard/templates/_partials/running.html
tests:
  - tests/factory_dashboard/test_overview.py
---

### Goal
Running now shows the goal of the ticket being worked on, and a run that waits names the waiting ticket's goal too.

### Context
Read `factory_dashboard/overview.py` (`Running`, `running_jobs`, `LiveRun`, `live_runs`), `factory_dashboard/templates/_partials/running.html` and the Running-now tests in `tests/factory_dashboard/test_overview.py` (`write_live` and `write_between_jobs` in `tests/factory_dashboard/conftest.py`).
- Facts: `tickets.title` is the first line of the ticket's Goal; the Queue panel already shows it. `running_jobs` doesn't select it, so the job card shows only the ticket id (`f2-11-review-bench`), which tells the owner nothing.
- Facts, the wait line: between jobs the run card reads `Running: {{ run.activity }}`, such as "waiting for Claude · f2-11-review-bench until 19:51". The runner writes `runs.activity` as plain text; the ticket id is the word after "· ". Look up that id in `tickets` (same project), and show its title on a second line under the activity. Show no second line when no ticket matches.
- Show the goal under the job card's head line, in normal text (not monospace). A job with no ticket (a checkpoint, a review) shows none.

### Done when
- a running job on a ticket shows that ticket's title in its card
- a checkpoint job shows no goal line
- a run waiting with activity "waiting for Claude · <ticket> until 19:51" shows that ticket's title under it; an activity naming no known ticket shows only the activity
- each assertion reads the card's own text, not the whole page
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2015
gate_failures: []
tokens: 2233419
```
