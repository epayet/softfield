---
id: f68-07-fix-cdn-regression-test-calls-helper-only
milestone: f68-i-want-the-factory-to-be
difficulty: 3
depends_on: []
files:
- tests/factory_dashboard/test_app.py
tests:
- tests/factory_dashboard/test_app.py
finding: f68-i-want-the-factory-to-be-C16-1
tests_only: true
---

### Goal
Fix a checkpoint finding on f68-06-fix-cdn-regression-test-still's tests: the CDN regression test still does not run the actual check.

### Context
By the lead at a checkpoint, on the merge of `.softfield/tasks/done/f68-06-fix-cdn-regression-test-still.md`. Change only tests. What was found is under Finding:
- f68-i-want-the-factory-to-be-C16-1, should-fix: `test_a_page_that_names_cdn_example_com_after_the_top_bar_fails` in `tests/factory_dashboard/test_app.py`.

### Finding
f68-i-want-the-factory-to-be-C16-1: f68-06 only added `assert found != []`, which the next assertion already implies; the test still calls `_find_third_party_hosts` and not the loop of `test_no_page_or_stylesheet_names_a_third_party_host` (`found == []`, no `@import`). If that test's body changed, this one would not notice. Move that body into one helper (for example `_third_party_problems(text)`) that both tests call; the regression test passes it the injected page and asserts it reports the cdn URL. Drop the redundant `found != []` assert.

### Done when
- each finding above no longer holds: the real test and the regression test share the one check, and the regression fails if that check stops flagging `https://cdn.example.com/x.js`
- the listed `tests:` pass, with no change outside `tests/`
- all gates pass

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1042
gate_failures: []
tokens: 463362
```
