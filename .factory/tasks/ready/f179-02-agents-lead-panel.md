---
id: f179-02-agents-lead-panel
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: [f179-01-lead-split]
files:
  - factory_dashboard/agents.py
  - factory_dashboard/templates/agents.html
  - factory_dashboard/static/dashboard.css
  - tests/factory_dashboard/test_agents.py
tests:
  - tests/factory_dashboard/test_agents.py
---

### Goal
The Agents page shows "Lead tickets, by model" after Efficiency, and "Who did what" shows every role that has a job.

### Context
The picture to build: `.factory/cards/f179-mockup/agents-lead-tickets.html` (Proposed). Read `.factory/cards/f179-how-is-sonnet-doing-as-an.md`, D4 and D5.
- The numbers: `lead_split` in `factory_dashboard/queries.py` (f179-01), for the page's project and milestone filter.
- Follow the page's own panels: `def agents_roles` and the route in `factory_dashboard/agents.py`, `factory_dashboard/templates/agents.html` (`agent-cell` rows with `--who`, `.panel` plate headers).
- The readout and the two bars: classes in `factory_dashboard/static/dashboard.css` from its existing tokens only (`--plate`, `--notch`, `--opus`, `--sonnet`); no new colour.

### Done when
- with Sonnet and Opus lead tickets, the panel shows the saving, the two bars to scale (Opus's would-have the full width) and one table row per agent and band, as the mock-up
- with no non-Opus lead ticket, there is no panel
- "Who did what" has lead-ticket and planner columns, in D5's order, and a role not in the list still gets a column, after the known ones
- the panel reads well at 390 px wide: the table scrolls, nothing overflows
- the listed `tests:` pass, and fail without the change
- all gates pass (see `docs/workflow.md`)
