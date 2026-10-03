---
id: f4-22-fix-belt-and-smoke-animations
milestone: f4-always-on
difficulty: 4
depends_on: []
files:
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_line.py
finding: f4-always-on-C228-2
---

### Goal
Fix a checkpoint finding on f3-03-line-motion: Belt and smoke animations do not apply on the phone floor

### Context
A should-fix finding (f4-always-on-C228-2) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-03-line-motion.md`: in `factory_dashboard/static/dashboard.css`, line 119. What it found is under Finding.

### Finding
> The motion selectors target `.floor`, but the visible phone diagram uses `.floor-phone`. Carrying belts and working-machine smoke therefore stay static on mobile, and the desktop-only reduced-motion test does not catch this.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
