# Milestone F270: test_shots.py stops waiting on real seconds

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-18.

## Notes
tests/runner/test_shots.py waits on the real page-readiness timeouts (12.5 s in test_a_slow_page_gets_its_pictures_and_no_readiness_request, about 5 s in three more): make those timeouts a parameter the tests set to a fraction of a second. From F71's review.

## What happens today (read 2026-11-18)
- **The 12.5 s is the test's own sleep, not a runner limit.** `test_a_slow_page_gets_its_pictures_and_no_readiness_request` gives its tiny app `time.sleep(6)` for a page that exists: two after pictures, 12 s. It was written (f85-05) to be "slower than the old 5 s check", a readiness request the runner no longer makes: `_serving` in `runner/shots.py` only checks that the port is open. And the test uses the `shoot` fake (a plain `urlopen` with no time limit), so the 6 s proves only that the fake waits. What the test still guards is that the app gets one request per picture and none for `/`.
- **The runner's limits are already settable.** `READY_LIMIT`, `PAGE_LIMIT`, `SETTLE_LIMIT` and `PICTURE_LIMIT` are module constants; `test_a_server_that_never_answers_is_recorded` already sets `READY_LIMIT` to 0.5 with `monkeypatch.setattr`. No new parameter is needed in `runner/shots.py` (protected).
- **The "about 5 s" tests** are most likely the real-Chromium ones whose page never goes quiet (`SETTLE_LIMIT`, 5 s, waits for `networkidle`): the page that submits a form, and the dashboard, which polls. F71's review didn't name them, so the ticket measures first.

## Decisions
- **D1. No change to `runner/shots.py`.** The tests set the module's limits with `monkeypatch.setattr`, as the `READY_LIMIT` test does. A parameter threaded through `take`/`_round`/`_browse` would change protected code for the tests' sake only.
- **D2. The slow-page test keeps its point, not its sleep:** a short delay (a fraction of a second) and the same request-count check. Its docstring stops citing the old 5 s check.
- **D3. A shorter `SETTLE_LIMIT` only where the test doesn't need the page to settle**, and each changed test must still fail when its behaviour is broken (a request the page makes after load must still be seen where a test asserts it).

## Done when
- `uv run pytest --durations=10 tests/runner/test_shots.py` shows no test over 3 s apart from the ones the developer's note names, each with why.
