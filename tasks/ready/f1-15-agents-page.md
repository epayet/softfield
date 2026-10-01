---
id: f1-15-agents-page
milestone: f1
depends_on: [f1-10-ticket-pages, f1-36-ticket-pages-fixes]
difficulty: 6
files:
  - factory_dashboard/agents.py
  - factory_dashboard/templates/agents.html
  - factory_dashboard/app.py
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
`/agents` compares the agents: how efficient each is, who did what, and their ratings over time.

### Context
Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with the fixture database in `tests/factory_dashboard/conftest.py` (extend it when your page needs more rows). The tables and columns are in `runner/metrics.py` (read it; it is the lead's file, so don't change it). Register your router in `factory_dashboard/app.py`. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put the rows your page needs in a function of your own (as `write_live` is), not among f1's or m4's tickets and jobs.
- Facts: who merged a ticket is `tickets.merged_by`, an agent id (`local-qwen3.6-35b-a3b`, `claude-opus`, or `backfill-unknown` when the backfill couldn't tell). A job's gates are JSON in `jobs.gates`, `[{"name", "ok", "seconds", "log"}]`. `rating_changes` stays empty until f1-24.
- **Efficiency,** a row per agent (optionally filtered by `milestone`): jobs, tickets merged, first-attempt pass rate, attempts per merge, minutes and tokens per merge, tokens per second, escalation rate, most-failed gate, dollars.
- **Who did what:** agents × roles, each cell the number of jobs.
- **Ratings:** one line per agent from `rating_changes` (coding and reviewing) over time, as a chart (D5 in `docs/milestones/f1.md`). Until ratings exist, an empty state says "Ratings start after f1-24".
- An agent with no merges shows dashes for per-merge numbers, not a division error.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the text the page shows, not only that it answers 200.

### Done when
- efficiency numbers for the fixture's local agent match a count by hand (write the expected numbers in the test)
- the agents × roles table has a cell per pair, empty pairs blank
- with no `rating_changes`, the empty state shows; with two changes, the chart's JSON has both points
- an agent with no merges shows dashes
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
