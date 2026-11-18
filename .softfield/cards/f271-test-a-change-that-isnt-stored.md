# Milestone F271: Two refused-edit tests check the request list instead of waiting 300 ms

> **State:** idea · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
test_a_change_that_isnt_stored_leaves_the_row_open (test_coming.py) and test_a_message_change_that_isnt_stored_leaves_the_editor_open (test_thread.py) still prove "no re-fetch followed" with wait_for_timeout(300): use watch_requests and requests_until from the dashboard tests' conftest, as f71-03 did for the other two. From F71's review.
