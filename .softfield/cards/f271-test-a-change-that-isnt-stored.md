# Milestone F271: Two refused-edit tests check the request list instead of waiting 300 ms

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
test_a_change_that_isnt_stored_leaves_the_row_open (test_coming.py) and test_a_message_change_that_isnt_stored_leaves_the_editor_open (test_thread.py) still prove "no re-fetch followed" with wait_for_timeout(300): use watch_requests and requests_until from the dashboard tests' conftest, as f71-03 did for the other two. From F71's review.

## Plan
One developer ticket, tests only: `f271-01-refused-edits-wait-on-requests`. It follows `test_a_failed_post_leaves_textarea_and_coming_as_they_were` (f71-03) in `tests/factory_dashboard/test_coming.py`. Nothing on screen changes, so there is no mock-up.
