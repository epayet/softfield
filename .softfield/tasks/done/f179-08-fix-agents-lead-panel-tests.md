---
id: f179-08-fix-agents-lead-panel-tests
milestone: f179-how-is-sonnet-doing-as-an
difficulty: 4
depends_on: []
files:
- tests/factory_dashboard/test_agents.py
tests:
- tests/factory_dashboard/test_agents.py
finding: f69-i-want-a-button-to-switch-C1849-4
tests_only: true
---

### Goal
Fix a checkpoint finding on f179-02-agents-lead-panel's tests: Panel and role tests assert presence, not the required content or behavior.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f179-02-agents-lead-panel.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1849-4, should-fix: in `tests/factory_dashboard/test_agents.py`.

### Finding
f69-i-want-a-button-to-switch-C1849-4: Panel and role tests assert presence, not the required content or behavior.
> `test_lead_panel_shows_with_non_opus_lead_ticket` checks labels and agent/band strings but not the actual saved/dollar values, each agent-band row's cell values, or bar widths; it would pass with incorrect totals and unscaled bars. Add coverage for the rendered 390px table scrolling without page overflow. `test_who_did_what_has_lead_ticket_and_planner_columns` checks only known headers; add an unlisted role and assert its column appears after the known roles.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1827
gate_failures: []
tokens: 2343628
```
