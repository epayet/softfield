---
id: f68-04-fix-the-cdn-regression-test
milestone: f68-i-want-the-factory-to-be
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1035-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f68-03-fix-the-third-party-host's tests: The CDN regression test does not exercise the third-party-host test

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.factory/tasks/done/f68-03-fix-the-third-party-host.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1035-1, should-fix: in `tests/factory_dashboard/test_app.py`, line 100.

### Finding
f69-i-want-a-button-to-switch-C1035-1: The CDN regression test does not exercise the third-party-host test
> The regression test duplicates the host-detection regex and asserts that the duplicate finds the injected URL; it never runs `test_no_page_or_stylesheet_names_a_third_party_host`. It would still pass if that test stopped detecting the URL, contrary to the Done when requiring the injected page to make the third-party-host test fail.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass
