---
id: f1-40-runs-agents-fixes
milestone: f1
depends_on: [f1-15-agents-page]
difficulty: 4
finding: f1-cp8
files:
  - factory_dashboard/runs.py
  - factory_dashboard/agents.py
  - factory_dashboard/static/charts.js
  - factory_dashboard/templates/run.html
  - tests/factory_dashboard/test_runs.py
  - tests/factory_dashboard/test_agents.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_runs.py
  - tests/factory_dashboard/test_agents.py
---

### Goal
`/runs` and `/runs/{run_dir}` tell running from stopped by the page's `now`, and `/agents` works with `?milestone=` and draws one rating line per agent; the tests check the numbers and statuses a person reads.

### Context
Read `factory_dashboard/runs.py`, `factory_dashboard/agents.py`, `tests/factory_dashboard/test_runs.py`, `tests/factory_dashboard/test_agents.py`, and how `factory_dashboard/overview.py` uses `now`.
- Facts, runs: `list_runs` takes `now` and ignores it; `_age` reads `datetime.now()`. The tests pin `NOW` (2026-10-02) in `get_now`, so a run's status depends on the wall clock. `test_a_run_with_fresh_heartbeat_shows_running` and `test_a_run_with_3_min_old_heartbeat_shows_stopped` only check that a word appears anywhere in the page (`"running" in html`), so they pass whatever the status. `write_runs` also writes a "stopped" run (`20260920-100000`) that no test reads. `list_runs` and `get_run` repeat the minutes and status logic. `factory_dashboard/templates/run.html` shows the Duration only `{% if run.minutes %}`. The list test checks only the first two rows; the stopped run's row and its `–` are not checked.
- Facts, agents: `efficiency()` adds `m.key = ?` when a milestone is given, but no query joins `milestones`, so `/agents?milestone=f1` raises an SQL error; no test passes `milestone`. The ticket asked for the same milestone condition in every query (the escalation count and `agents_roles` ignore it). The ticket asked for one rating line per agent; the `rating` kind in `factory_dashboard/static/charts.js` draws one per skill, mixes agents, leaves `agents` unused, and its tooltip prints `p[0].data2`, which is never set. `test_efficiency_numbers_for_fixture_local_agent` checks `"5" in eff`, `"2" in eff`, `"3" in eff` on the whole section's text, which any row satisfies; `test_claude_sonnet_shows_dashes_for_per_merge` checks `"1"` and `"–"` anywhere in the section, which the local row satisfies too.

### Done when
- a run's status (running, stopped, done) is computed from the injected `now`, in one place used by both pages; the list shows it too
- tests: a run with a 30 s heartbeat shows `running` and one with a 3 min heartbeat shows `stopped`, each asserted in that run's own list row and in the `info` section of its page (the other word absent); every row of the list is checked for its run, minutes (or a dash) and verdict or status
- `/agents?milestone=f1` answers 200 with every query filtered by it; a test compares one number against `/agents` without a filter (the `m4-01-old` merge drops out of the local row)
- the rating chart has one series per agent, named by the agent; a test checks the JSON still carries both points
- the efficiency test reads the local agent's row cell by cell (jobs 5, merged 2, attempt tickets 3, 67%, 2.5, 25.0, 287500, 192, 33%, `$0.00`, dash) and the `claude-sonnet` test reads its own row (1 job, 0 merged, dashes); no bare `"5" in eff`
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1624
gate_failures: []
tokens: 2823283
```
