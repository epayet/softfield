---
id: f179-07-fix-agents-lead-panel
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: []
files:
- factory_dashboard/agents.py
tests:
- tests/factory_dashboard/test_agents.py
finding: f69-i-want-a-button-to-switch-C1849-3
---

### Goal
Fix a checkpoint finding on f179-02-agents-lead-panel: The panel's Sonnet totals include Opus-owned tickets, and its bar styling does not apply.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f179-02-agents-lead-panel.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1849-3, should-fix: in `factory_dashboard/agents.py`, line 259.

### Finding
f69-i-want-a-button-to-switch-C1849-3: The panel's Sonnet totals include Opus-owned tickets, and its bar styling does not apply.
> The Done when says “with Sonnet and Opus lead tickets, the panel shows the saving, the two bars to scale (Opus's would-have the full width)”. `total_dollars` sums every row, including Opus's, so the Sonnet amount and percentage are incorrect. The CSS rules in `factory_dashboard/static/dashboard.css` target `.panel.lead`, but the template section has only `class="panel"`; consequently the bar fill and 390px table rules do not apply. Even if the selector is fixed, `.fill { flex: 1 1 0 }` gives the bars equal flex widths instead of scaling to their inline percentages.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
