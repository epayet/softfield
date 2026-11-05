---
id: f81-13-fix-send-order-keeps-its
milestone: f81-assess-the-current-ui-state-of
agent: lead
difficulty: 1
depends_on: []
files:
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1830-1
---

### Goal
Fix a checkpoint finding on f81-09-send-order-keeps-its-colour: Disabled Send new order button loses its plate colour

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f81-09-send-order-keeps-its-colour.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1830-1, should-fix: in `factory_dashboard/static/dashboard.css`, line 1148.

### Finding
f69-i-want-a-button-to-switch-C1830-1: Disabled Send new order button loses its plate colour
> The later `.btn.go:disabled` rule has the same specificity as `.projects-page .send-order:disabled`, so it overrides the page rule and makes the disabled button transparent with a dashed border. This breaks the ticket Goal: “stays the plate colour while it is disabled.”

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
