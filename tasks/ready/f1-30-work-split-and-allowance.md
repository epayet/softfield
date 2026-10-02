---
id: f1-30-work-split-and-allowance
milestone: f1
depends_on: [f1-25-router, f1-48-ticket-work-split, f1-58-overview-factory]
difficulty: 5
files:
  - factory_dashboard/milestones.py
  - factory_dashboard/templates/milestone.html
  - factory_dashboard/overview.py
  - factory_dashboard/templates/overview.html
  - factory_dashboard/static/charts.js
  - tests/factory_dashboard/conftest.py
tests:
  - tests/factory_dashboard/test_milestones.py
  - tests/factory_dashboard/test_overview.py
---

### Goal
The milestone page and the Overview show who did the work, as each agent's share, and each allowance before and after the milestone.

### Context
Read `docs/adr/15-allowance-aware-routing.md` item 13. Follow the worked example: `factory_dashboard/overview.py`, `factory_dashboard/templates/overview.html` and `tests/factory_dashboard/test_overview.py`, with charts drawn as in `factory_dashboard/static/charts.js` (a `data-chart` div plus a JSON block). f1-48 built the per-ticket version (`factory_dashboard/tickets.py`): reuse its query shape. `write_fixture`'s numbers are pinned by `tests/factory_dashboard/test_queries.py` and `tests/factory_dashboard/test_overview.py`: put your rows in a function of your own in `tests/factory_dashboard/conftest.py`, as `write_live` is.
- **Work split, on the milestone page:**
  - per agent: tickets merged (by `tickets.merged_by`), lines changed (the merged tickets' `lines_changed`), attempts (its jobs with role `developer` or `last-attempt`), minutes, tokens and dollars
  - shown as a stacked bar of lines by agent, plus a table
- **Allowance before and after,** on the same page:
  - for each agent with readings, its `usage_events` of kind `reading` (f1-44: a `window` column, `value` from 0 to 1, `resets_at`) from the milestone's first job to its last, as a line per window on one timeline
  - readings come from Claude (`five_hour`, `seven_day`, f1-44) and Copilot (`month`, f1-22); the Ollama agents have none (no usage API, f1-18's probe)
  - an agent with only refusals shows them as marks; one with none says "no data yet"
- **Overview** (f1-58 made it the factory; its allowance panel stays below the floor): the same split for the current milestone, as one compact bar. It replaces Claude's allowance bar (`claude_allowance` in `factory_dashboard/overview.py`) with each agent's windows, each with its latest reading and its reset: Claude's 5 h and week (the week marked at `[claude] reserve` in `workflow/runner.toml`), Copilot's month. The owner asked for this on 2026-10-02: the Overview didn't say what the allowances are.

**The dashboard is English-only: no gettext and no French.** Tests use `TestClient` and check the JSON each chart renders and the table's cells, not only that the page answers 200.

### Done when
- a milestone worked by two agents shows each one's tickets, lines and dollars, in the table and in the chart's JSON
- readings from before and after the milestone appear on its timeline, per window
- an agent with no readings says "no data yet"
- the Overview shows the latest reading per window with its reset
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
