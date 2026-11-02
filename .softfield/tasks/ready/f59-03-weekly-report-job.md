---
id: f59-03-weekly-report-job
milestone: f59-periodic-review-of-the-factory
difficulty: 6
depends_on: [f59-01-reports-week-numbers]
agent: lead
files:
  - runner/loop.py
  - runner/prompts.py
  - runner/claude.py
  - factory_dashboard/reports.py
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
tests:
  - tests/runner/test_loop.py
  - tests/runner/test_prompts.py
---

### Goal
Once a week, at the first pick after Claude's seven-day allowance comes back, the runner runs a `report` job that writes the week just ended as `.softfield/reports/<monday>.md` and commits it.

### Context
Read `.softfield/cards/f59-periodic-review-of-the-factory.md` (D5, D6, D7). Write the tests first.
- Follow the planner job: `run_planner` and `run_queued` in `runner/loop.py`, `PLANNER` in `runner/prompts.py`, and how `runner/claude.py` scopes a job's tools.
- The reset is read from `usage_events` (`seven_day`, `resets_at`); the week before has a file or it doesn't, so the job runs once per week even across restarts.
- The brief, `REPORT`, gets the numbers of `week` in `factory_dashboard/reports.py` for the whole factory and for each project with jobs that week, as text, and asks for D6's sections and D7's quoted ideas.
- The agent is `[roles] report`'s, else the first `[roles] review` names.

### Done when
- with a reading showing the window reset after Monday 2 Nov 00:00 and no `.softfield/reports/2026-10-26.md`, the next pick queues one `report` job; with the file there, none
- a second pick in the same week queues nothing, a restart included
- the job runs under Claude's reserve, as a planner job does, and its tools let it write only `.softfield/reports/*`
- the runner commits the file on the factory's own project's main ("Report for the week of 26 Oct"); a job that wrote nothing commits nothing and is a failed job
- `REPORT` carries every scope's numbers and names the sections and the quoted-idea form
- with no `[roles] report`, the job runs on the first agent `[roles] review` names
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
