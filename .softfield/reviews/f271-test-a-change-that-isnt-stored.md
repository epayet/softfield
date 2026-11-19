# Review: F271, two refused-edit tests check the request list instead of waiting 300 ms

- **Status:** review done (round 1), no findings, waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- Nothing on screen. Two dashboard tests (a refused change to a waiting plant on Planning, a refused change to a waiting message on a thread) no longer wait 300 ms and hope; they read the page's own list of requests and check that only the refused post was sent.
- A wrongful re-fetch now fails the test every time, however late or fast it is, the same way f71-03's two tests already did.

### 2. How to test it yourself
1. Run `uv run pytest -q tests/factory_dashboard/test_coming.py tests/factory_dashboard/test_thread.py -k isnt_stored`: two tests pass in a few seconds.
2. Optional: in `factory_dashboard/templates/planning.html`, drop `&& event.detail.successful` from the waiting-plant branch and run step 1 again: the Planning test fails on the request list.

### 3. Done when, as of now
- **Met:** both tests use `watch_requests` and `requests_until` from the dashboard tests' conftest, as f71-03 did, and no `wait_for_timeout(300)` is left in them. The review checked that the page's re-fetch listeners sit on the document from page load, so a re-fetch would show between the post's two entries and break the exact-list assert.

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:** nothing new from this milestone.

<!-- runner report -->
<!-- /runner report -->
