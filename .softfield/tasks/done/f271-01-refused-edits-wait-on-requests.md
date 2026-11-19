---
id: f271-01-refused-edits-wait-on-requests
milestone: f271-test-a-change-that-isnt-stored
difficulty: 1
files:
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_thread.py
tests:
  - tests/factory_dashboard/test_coming.py
  - tests/factory_dashboard/test_thread.py
tests_only: true
---

### Goal
The two refused-edit tests prove "no re-fetch followed" from the page's own list of requests, not from a 300 ms wait a late re-fetch could slip past.

### Context
- The two tests: `test_a_change_that_isnt_stored_leaves_the_row_open` in `tests/factory_dashboard/test_coming.py` and `test_a_message_change_that_isnt_stored_leaves_the_editor_open` in `tests/factory_dashboard/test_thread.py`. Each ends its post with `page.wait_for_timeout(300)` before asserting.
- The pattern to follow is `test_a_failed_post_leaves_textarea_and_coming_as_they_were` in `tests/factory_dashboard/test_coming.py`: `watch_requests(page)` before the click, then `requests_until(page, "afterRequest post /requests")` and an assert that the list holds only the post's two entries. Both helpers are in `tests/factory_dashboard/conftest.py`; `test_thread.py` doesn't import them yet.
- Both Save buttons submit an htmx form (`hx-post="/requests"`: `edit-<id>` in `factory_dashboard/templates/planning.html`, `editor-<id>` in `factory_dashboard/templates/thread.html`), so the watcher sees them.
- Change no test's meaning: each still checks the editor keeps what was typed and nothing is stored. The templates don't change.

### Done when
- neither test calls `wait_for_timeout`
- each asserts the requests list is exactly `["beforeRequest post /requests", "afterRequest post /requests"]`
- each still fails when a request follows the refused post (try it once, e.g. have the page send an htmx GET on `htmx:afterRequest`, and see it fail)
- the listed `tests:` pass on 16 workers (`-n 16`)
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 1200
gate_failures: []
tokens: 872525
```
