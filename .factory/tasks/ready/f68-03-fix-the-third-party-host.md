---
id: f68-03-fix-the-third-party-host
milestone: f68-i-want-the-factory-to-be
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1026-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f68-02-brand-tests-check-content's tests: The third-party-host test exempts more than the SVG namespace.

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f68-02-brand-tests-check-content.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1026-1, should-fix: in `tests/factory_dashboard/test_app.py`, line 94.

### Finding
f69-i-want-a-button-to-switch-C1026-1: The third-party-host test exempts more than the SVG namespace.
> The test excludes `http://www.w3.org` as well as `http://www.w3.org/2000/svg`, so other URLs at that host can escape detection. It also never injects the specified `https://cdn.example.com/x.js` after the top bar to verify that case fails. Check only the exact namespace URL and add the regression case required by the ticket’s Done when: “a page that names `https://cdn.example.com/x.js` after the top bar makes the third-party host test fail.”

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
