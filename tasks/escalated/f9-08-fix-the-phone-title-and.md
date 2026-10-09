---
id: f9-08-fix-the-phone-title-and
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- factory_dashboard/static/dashboard.css
tests:
- tests/factory_dashboard/test_app.py
finding: f9-line-polish-C423-1
---

### Goal
Fix a checkpoint finding on f3-30-phone-top-bar: The phone title and project filter are stacked instead of sharing one line.

### Context
A should-fix finding (f9-line-polish-C423-1) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-30-phone-top-bar.md`: in `factory_dashboard/static/dashboard.css`, line 220. What it found is under Finding.

### Finding
> The mobile rule sets `.bar-top` to `flex-direction: column`, directly contradicting f3-30’s requirement that the title and filter share a line. The height assertion does not catch this layout failure.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass

```yaml
# --- runner ---
result: escalated
reason: gates failed 3x (last: tests-fail-on-main)
attempts: 3
tokens: 1495691
logs: var/runs/20261009-020915/f9-08-fix-the-phone-title-and
```
