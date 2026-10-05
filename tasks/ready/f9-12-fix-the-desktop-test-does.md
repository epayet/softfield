---
id: f9-12-fix-the-desktop-test-does
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f9-line-polish-C423-5
---

### Goal
Fix a checkpoint finding on f3-30-phone-top-bar: The desktop test does not verify that tabs fit without scrolling.

### Context
A should-fix finding (f9-line-polish-C423-5) by copilot-auto, standing in for the lead at a checkpoint, on the merge of `tasks/done/f3-30-phone-top-bar.md`: in `tests/factory_dashboard/test_app.py`, line 242. What it found is under Finding.

### Finding
> The test checks that tab links appear in the HTML, but does not render at 1440 px or inspect the tab container’s overflow. It would pass if the tabs were present but required horizontal scrolling.

### Done when
- what the finding describes no longer holds, and a test shows it
- the listed `tests:` pass, and fail without the change
- all gates pass
