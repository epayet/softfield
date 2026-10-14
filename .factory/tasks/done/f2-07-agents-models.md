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
Read `factory_dashboard/agents.py` (`efficiency`, `agents_page`), its template and `tests/factory_dashboard/test_agents.py`. f2-04 added `jobs.model` (NULL on older jobs).
- Each agent keeps its own efficiency row exactly as today, totals over all its models: the existing tests in `tests/factory_dashboard/test_agents.py` pin those rows and must pass unchanged.
- Right under an agent's row, add one row per distinct `model` of that agent's jobs, with the same columns computed over that model's jobs only. NULL and `''` are one group, shown as "not recorded".
- An agent whose jobs all have one model (or all have none) gets no extra rows. Every agent in `write_fixture` is like that, so the default page looks as before.
- Fixture rows: `runner.metrics.start_job` and `finish_job` both take `model=`, and conftest's `_job(...)` passes extra keywords to `finish_job`, so `_job(..., model="claude-sonnet-4-5")` works. `write_fixture` has one `claude-sonnet` job (a checkpoint, no model).
- Put your rows in a function of your own in `tests/factory_dashboard/conftest.py` with a fixture client beside it, as `write_allowance` and `allowance_client` are; the test takes that fixture as a parameter.

**The dashboard is English-only and never writes the database.**

`check-all` takes several minutes: give its shell call a timeout of 900000 ms, or it is killed with "(no output)" (your last attempt stopped there).

### Done when
- `claude-sonnet` with jobs on two models shows its own row, then a row per model with that model's job count and dollars
- jobs without a model show under "not recorded"
- an agent on a single model shows no model rows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: needs-info
attempts: 1
tokens: 752269
logs: var/runs/20261002-151301/f2-07-agents-models
```

```yaml
# --- runner ---
result: escalated
reason: BLOCKED: needs-file
attempts: 1
tokens: 1095940
logs: var/runs/20261002-151301/f2-07-agents-models-run2
```

```yaml
# --- runner ---
result: done
finished_by: lead
```
