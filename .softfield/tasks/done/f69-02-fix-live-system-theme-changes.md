---
id: f69-02-fix-live-system-theme-changes
milestone: f69-i-want-a-button-to-switch
area: factory
difficulty: 3
depends_on: []
files:
- factory_dashboard/templates/base.html
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1026-2
---

### Goal
Fix a checkpoint finding on f69-01-theme-button: Live system-theme changes leave the button and charts out of sync.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f69-01-theme-button.md`. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1026-2, should-fix: in `factory_dashboard/templates/base.html`, line 17.

### Finding
f69-i-want-a-button-to-switch-C1026-2: Live system-theme changes leave the button and charts out of sync.
> The system-preference listener updates `data-theme` but does not update the button label or dispatch `themechange`; charts only redraw on that event. Thus when the system preference changes with nothing stored, the page follows the system visually but charts retain the old colors and the button names the wrong theme to switch to. This breaks the ticket’s Done when: “with nothing stored, the page follows the system” and its requirement that the button name the theme it switches to.

### Done when
- what each finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 5855
gate_failures: []
tokens: 855815
```
