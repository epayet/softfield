---
id: f179-07-fix-agents-lead-panel
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: []
files:
- factory_dashboard/agents.py
- factory_dashboard/templates/agents.html
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_agents.py
finding: f69-i-want-a-button-to-switch-C1849-3
---

### Goal
Fix a checkpoint finding on f179-02-agents-lead-panel: The panel's Sonnet totals include Opus-owned tickets, and its bar styling does not apply.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f179-02-agents-lead-panel.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1849-3, should-fix: in `factory_dashboard/agents.py`, line 259.

The data behind `lead_client` is `write_fixture` plus `write_lead_tickets`, both in `tests/factory_dashboard/conftest.py`. `write_fixture` already holds `f1-03-lead`, an Opus lead ticket at difficulty 4 costing $3.00, so the Sonnet ticket's would-have is $3.00. The panel's values are: Sonnet $0.50, Opus would have $3.00, saved $2.50, Sonnet bar 17%.

### Finding
f69-i-want-a-button-to-switch-C1849-3: The panel's Sonnet totals include Opus-owned tickets, and its bar styling does not apply.
> The Done when says “with Sonnet and Opus lead tickets, the panel shows the saving, the two bars to scale (Opus's would-have the full width)”. `total_dollars` sums every row, including Opus's, so the Sonnet amount and percentage are incorrect. The CSS rules in `factory_dashboard/static/dashboard.css` target `.panel.lead`, but the template section has only `class="panel"`; consequently the bar fill and 390px table rules do not apply. Even if the selector is fixed, `.fill { flex: 1 1 0 }` gives the bars equal flex widths instead of scaling to their inline percentages.

### Done when
- with `lead_client`, the `lead` section of the page says Sonnet $0.50, Opus would have $3.00 and $2.50 saved, and its Sonnet bar has `width:17%`; each check reads that section only, not the whole page
- the `lead` section carries the `lead` class
- a browser test at a 1280 px wide viewport: the Sonnet `.fill`'s rendered width divided by the Opus `.fill`'s is about 0.17 (within 0.02), and both bars' labels are visible
- the listed `tests:` pass, and fail without the change
- all gates pass
