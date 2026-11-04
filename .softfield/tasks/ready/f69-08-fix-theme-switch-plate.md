---
id: f69-08-fix-theme-switch-plate
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_app.py
finding: f81-assess-the-current-ui-state-of-C1743-1
---

### Goal
Fix a checkpoint finding on f69-07-theme-switch-plate: Phone plate sizing rule never applies

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f69-07-theme-switch-plate.md`. What it found is under Finding:
- f81-assess-the-current-ui-state-of-C1743-1, should-fix: in `factory_dashboard/static/dashboard.css`, line 413.

### Finding
f81-assess-the-current-ui-state-of-C1743-1: Phone plate sizing rule never applies
> The ticket's Goal calls for “a compact upright switch” and its phone requirement specifies a 24 × 40 px plate. These overrides require a `.phone` ancestor, but the app does not add that class at mobile widths; at 390 px the plate stays 36 px tall and the phone-specific knob sizing is skipped.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
