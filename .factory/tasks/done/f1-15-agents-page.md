---
id: f1-15-agents-page
milestone: f1
depends_on: [f1-10-ticket-pages, f1-36-ticket-pages-fixes]
difficulty: 6
files:
  - factory_dashboard/agents.py
  - factory_dashboard/templates/agents.html
  - factory_dashboard/app.py
  - factory_dashboard/static/charts.js
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
`/agents` compares the agents: how efficient each is, who did what, and their ratings over time.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py`. The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`.
- Facts: who merged a ticket is `tickets.merged_by`, an agent id (`local-qwen3.6-35b-a3b`, `claude-opus`, or `backfill-unknown` when the backfill couldn't tell). A job's gates are JSON in `jobs.gates`, `[{"name", "ok", "seconds", "log"}]`. `rating_changes` stays empty until f1-24.
- **Efficiency,** a row per agent that has any job in the project (optionally filtered by `milestone`; with no filter, every milestone counts, so apply the milestone condition only when a filter is given, the same way in every query). Definitions:
  - jobs: all its jobs, any role. Merged: tickets whose `merged_by` is the agent.
  - attempt tickets: tickets where it has a `developer` or `last-attempt` job. First-attempt pass rate: share of attempt tickets with exactly one such job, which passed. Attempts per merge: its `developer` + `last-attempt` jobs ÷ merged.
  - minutes per merge: sum of its jobs' durations (ended − started) ÷ merged. Tokens per merge: sum of `tokens_in` + `tokens_cached` + `tokens_out` ÷ merged. Tokens per second: those tokens ÷ the summed durations in seconds.
  - escalation rate: share of its attempt tickets that have an `escalation` job (by any agent). Most-failed gate: the gate name with `ok` false most often across its jobs. Dollars: sum of `cost_usd`.
  - a rate or per-merge number whose denominator is zero shows a dash.
- **Who did what:** agents × roles, each cell the number of jobs.
- **Ratings:** one line per agent from `rating_changes` (coding and reviewing) over time, as a chart (D5 in `docs/milestones/f1.md`: add a kind to `factory_dashboard/static/charts.js`). Until ratings exist, an empty state says "Ratings start after f1-24".

**The efficiency test uses `write_fixture` exactly as it is:** take the client from `serve(live=False)`, since the plain `client` fixture adds `write_live`'s rows, including a running local job at `f1-04-live` that would change every count below. The local agent's jobs in `write_fixture`, all from `_job`, which runs every job 10:00 to 10:10, so each lasts 600 seconds:

| ticket | role | tokens (in + out) |
|---|---|---|
| f1-01-first (merged by local) | developer, passed | 200,000 + 10,000 |
| f1-02-escalated (merged by claude-opus) | developer, failed | 100,000 + 5,000 (`_local`) |
| f1-02-escalated | developer, failed | 100,000 + 5,000 (`_local`) |
| f1-02-escalated | last-attempt, failed | 100,000 + 5,000 (`_local`) |
| m4-01-old (merged by local) | developer, passed | 50,000 + 0 |

That is 5 jobs, 3,000 seconds, 575,000 tokens (f1's 4 jobs are 500,000 in + 25,000 out, pinned by `test_milestone_results_split_local_and_claude_spend` in `tests/factory_dashboard/test_queries.py`), and none has gates or a cost. So local over all milestones is: 5 jobs, 2 merged, 3 attempt tickets, first pass 2/3 (67%), 2.5 attempts per merge, 25.0 minutes per merge, 287,500 tokens per merge, 192 tokens per second (575,000 ÷ 3,000 = 191.7), escalation 1/3 (33%), no failed gate (dash), $0. `claude-sonnet` (one checkpoint, no merges) is the no-merges row: per-merge numbers show dashes, not a division error.

The empty-state test can use the plain `client` (no `rating_changes`). The chart test needs two rating changes of its own: add them in a new function in `tests/factory_dashboard/conftest.py` (as `write_project` is, with a fixture like `project_client`). `write_fixture`'s numbers are pinned by other tests; don't change its rows, and define each new fixture name once.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

If your count differs from the numbers above, recount from the table: they were checked against a passing test. Don't change fixture rows to make a number fit.

### Done when
- efficiency numbers for the fixture's local agent match the numbers above (write them in the test)
- the agents × roles table has a cell per pair, empty pairs blank
- with no `rating_changes`, the empty state shows; with two changes, the chart's JSON has both points
- `claude-sonnet` shows dashes for its per-merge numbers
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: ruff)
attempts: 3
tokens: 10655080
logs: var/runs/20261001-082453/f1-15-agents-page
```

```yaml
# --- runner ---
result: escalated
reason: pre-flight failed
attempts: 0
tokens: 0
logs: var/runs/20261001-082453/f1-15-agents-page-run2
```

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 4248
gate_failures: ['no-changes']
tokens: 8760968
```
