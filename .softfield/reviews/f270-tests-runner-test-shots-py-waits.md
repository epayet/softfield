# Review: F270, test_shots.py stops waiting on real seconds

- **Status:** review done (round 1), waiting for the owner's sign-off.

## Sign-off sheet

### 1. What changed
- The slow-page test in `tests/runner/test_shots.py` sleeps 0.4 s instead of 6 s per page: it went from 12.5 s to 1.25 s and still checks one request per picture and none for `/`.
- The three real-Chromium tests still take about 5 s each, and now say why in a comment: two browser starts plus Playwright's 500 ms of quiet per picture, not a limit the tests could shorten.

### 2. How to test it yourself
1. Run `uv run pytest --durations=8 tests/runner/test_shots.py`.
2. The slow-page test shows about 1 s; only the Chromium tests (about 5 s, three of them) and the dashboard one (about 3 s) are above it, as the comment above them explains.

### 3. Done when, as of now
- **Met:** no test over 3 s apart from the ones named with why: the three real-Chromium tests (about 5 s) and the dashboard picture test (about 3.2 s), explained in the comment above the Chromium tests.

### 5. Decisions made along the way
- **The Chromium tests keep their 5 s.** Their limits aren't what they wait on: with no settling at all a test takes 1.6 s, and the rest is Playwright's 500 ms network-idle floor per picture. Cutting pictures from the tests would weaken them for about 10 s of a parallel run. *The review.*

### 6. What next
- **Product:** product work is on hold; nothing to suggest.
- **Factory:**
  - A ticket that asks for before/after durations should get them checked by the gates, not taken on trust: here the developer's three "faster" tests weren't faster at all.
    > When a ticket's Done when asks for a measurement (durations before and after), the runner should refuse the result unless the developer's final note carries both numbers, so a no-op change like F270's limit patches can't pass unmeasured.

### 8. How the work went
- Half the diff (six `monkeypatch.setattr` lines) did nothing, because the browser runs in its own process; the planner's guess that `SETTLE_LIMIT` cost the 5 s was also wrong. One timed run before and after would have caught both; the review measured, removed the lines and wrote the reason down.

### 9. What clogged the factory line
- **41.5 min of model time** for a 10-line test change (1.2M tokens in), mostly running the slow test file; the Chromium tests' 5 s each is now documented, so the next ticket won't chase it.

<!-- runner report -->
<!-- /runner report -->
