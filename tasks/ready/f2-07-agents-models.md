---
id: f2-07-agents-models
milestone: f2
depends_on: [f2-04-job-model]
difficulty: 3
files:
  - factory_dashboard/agents.py
  - factory_dashboard/templates/agents.html
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
The Agents page splits each agent's results by the exact model it ran on, so a new model version can be compared with the old one.

### Context
Read `factory_dashboard/agents.py` (`efficiency`, `agents_page`), its template and `tests/factory_dashboard/test_agents.py`. f2-04 added `jobs.model` (empty on older jobs).
- Under each agent's efficiency row, one row per distinct `model` (empty shows as "not recorded"): jobs, first-attempt passes, average minutes, dollars, the same columns as the agent's row.
- An agent with a single model shows no extra rows.
- Put your fixture rows in a function of your own in `tests/factory_dashboard/conftest.py`, as `write_live` is.

**The dashboard is English-only and never writes the database.**

### Done when
- `claude-sonnet` with jobs on two models shows a row per model with its own counts
- jobs without a model show under "not recorded"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
