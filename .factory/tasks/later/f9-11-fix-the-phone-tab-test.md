---
id: f9-11-fix-the-phone-tab-test
milestone: f9-line-polish
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f9-line-polish-C423-4, f9-line-polish-C423-5
tests_only: true
---

### Goal
Fix 2 checkpoint findings on f3-30-phone-top-bar's tests: The phone tab test scrolls the active tab itself before checking visibility; The desktop test does not verify that tabs fit without scrolling.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f3-30-phone-top-bar.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f9-line-polish-C423-4, should-fix: in `tests/factory_dashboard/test_app.py`, `test_phone_top_bar_is_compact_and_tabs_scroll`.
- f9-line-polish-C423-5, should-fix: in `tests/factory_dashboard/test_app.py`, `test_desktop_bar_unchanged_at_1440`.
- The page scrolls the current tab into view itself, in `factory_dashboard/templates/base.html`. `open_overview` in `tests/factory_dashboard/test_overview.py` serves only `/` and `/live` to the browser: a page whose tab sits past a phone's width needs its own route, built the same way.

### Finding
f9-line-polish-C423-4: The phone tab test scrolls the active tab itself before checking visibility.
> Calling `scrollIntoView` in the test masks whether the page’s automatic active-tab scrolling works. It loads Overview, whose first tab is already visible, so the test would pass even if the template’s scrolling behavior were missing.

f9-line-polish-C423-5: The desktop test does not verify that tabs fit without scrolling.
> The test checks that tab links appear in the HTML, but does not render at 1440 px or inspect the tab container’s overflow. It would pass if the tabs were present but required horizontal scrolling.

### Done when
- at 390 px, a page whose tab is past the visible width when the tabs aren't scrolled (the last tab's page, such as `/bench`) shows that tab within `nav.tabs`' visible width, with no scrolling and no waiting by the test: it would fail if the page didn't scroll the tab into view
- in a browser at 1440 px wide, `nav.tabs`' `scrollWidth` is at most its `clientWidth` and the host address (`.brand small`) is visible: it would fail if the tabs needed scrolling
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
