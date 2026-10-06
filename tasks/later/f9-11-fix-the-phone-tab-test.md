---
id: f9-11-fix-the-phone-tab-test
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f9-line-polish-C423-4
---

### Goal
Fix a checkpoint finding on f3-30-phone-top-bar: The phone tab test scrolls the active tab itself before checking visibility.

### Context
A should-fix finding (f9-line-polish-C423-4) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-30-phone-top-bar.md`: in `tests/factory_dashboard/test_app.py`, line 225. What it found is under Finding.

### Finding
> Calling `scrollIntoView` in the test masks whether the page’s automatic active-tab scrolling works. It loads Overview, whose first tab is already visible, so the test would pass even if the template’s scrolling behavior were missing.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
