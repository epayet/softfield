---
id: f4-17-agents-model-label
milestone: f4-always-on
depends_on: []
difficulty: 2
files:
  - factory_dashboard/agents.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
On the Agents page, the per-model rows for jobs with no recorded model say why, instead of a bare "not recorded".

### Context
Read `factory_dashboard/agents.py` (`NOT_RECORDED`, `efficiency`) and the model-split tests in `tests/factory_dashboard/test_agents.py` (`write_models` in `tests/factory_dashboard/conftest.py`).
- Facts: jobs are grouped by `jobs.model`; NULL or '' becomes "not recorded". Models have been recorded only since 2026-10-02 (f2-04), so these rows are older jobs, which the owner can't tell.
- The label becomes "before 2 Oct (model not recorded)".

### Done when
- an agent with jobs on two models and older jobs with no model shows a row labelled "before 2 Oct (model not recorded)"
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
