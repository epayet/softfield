---
id: f68-06-fix-cdn-regression-test-still
milestone: f68-i-want-the-factory-to-be
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f68-i-want-the-factory-to-be-C1080-3
tests_only: true
---

### Goal
Fix a checkpoint finding on f68-05-fix-cdn-regression-test-duplicates's tests: CDN regression test still bypasses the actual check

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f68-05-fix-cdn-regression-test-duplicates.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f68-i-want-the-factory-to-be-C1080-3, should-fix: in `tests/factory_dashboard/test_app.py`, line 132.

### Finding
f68-i-want-the-factory-to-be-C1080-3: CDN regression test still bypasses the actual check
> The test runs `_find_third_party_hosts` on the injected HTML and asserts the helper detects the URL; it never invokes `test_no_page_or_stylesheet_names_a_third_party_host`. It can pass even if that regression test stops detecting third-party hosts. Run the injected page through the actual check and assert that the check fails, as required by the ticket’s Done when.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2802
gate_failures: []
tokens: 207434
```
