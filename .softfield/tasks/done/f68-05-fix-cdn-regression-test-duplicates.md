---
id: f68-05-fix-cdn-regression-test-duplicates
milestone: f68-i-want-the-factory-to-be
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f69-i-want-a-button-to-switch-C1044-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f68-04-fix-the-cdn-regression-test's tests: CDN regression test duplicates the detector instead of exercising it

### Context
By copilot-auto, standing in for the lead at a checkpoint, on the merge of `.softfield/tasks/done/f68-04-fix-the-cdn-regression-test.md`. It found the code right and its tests weak: change only tests. They pass on main's code, as they should. What it found is under Finding:
- f69-i-want-a-button-to-switch-C1044-1, should-fix: in `tests/factory_dashboard/test_app.py`, line 100.

### Finding
f69-i-want-a-button-to-switch-C1044-1: CDN regression test duplicates the detector instead of exercising it
> The test runs its own copy of the host-detection regex against injected HTML; it never invokes `test_no_page_or_stylesheet_names_a_third_party_host`. It would still pass if that regression test stopped detecting the URL. Make the injected page run through the actual check and assert that it fails.

### Done when
- each finding above no longer holds: the tests it names check content, and would fail if the code were wrong
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 2
duration_s: 3720
gate_failures: []
tokens: 353667
```
