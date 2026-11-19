---
id: f270-01-quick-shots-tests
milestone: f270-tests-runner-test-shots-py-waits
agent: developer
difficulty: 2
depends_on: []
tests_only: true
files:
  - tests/runner/test_shots.py
tests:
  - tests/runner/test_shots.py
---

### Goal
`tests/runner/test_shots.py` stops waiting on real seconds: the slow-page test drops its 6 s sleep and the tests that sit out `SETTLE_LIMIT` set it to a fraction of a second, with the same checks.

### Context
Read "What happens today" and D1–D3 in `.softfield/cards/f270-tests-runner-test-shots-py-waits.md`. Then the limits at the top of `runner/shots.py` (`READY_LIMIT`, `PAGE_LIMIT`, `SETTLE_LIMIT`, `PICTURE_LIMIT`) and `draw` inside `_browse`, which waits for `networkidle` up to `SETTLE_LIMIT`. Follow `test_a_server_that_never_answers_is_recorded`, which sets `READY_LIMIT` with `monkeypatch.setattr`. Don't change `runner/shots.py`.

### Done when
- measured first on main: your final note gives `uv run pytest --durations=15 tests/runner/test_shots.py`, before and after
- `test_a_slow_page_gets_its_pictures_and_no_readiness_request` delays its page by under half a second and still checks one request per picture and none for `/`; its docstring no longer cites the old 5 s check
- each test that spent about 5 s waiting on a limit sets that limit to under a second with `monkeypatch`, and still checks everything it checked (in the real-Chromium test, `GET /redirect` and `GET /dark-theme` are still seen)
- no test in the file takes over 3 s, or your final note names each one left and why
- each changed test still fails when what it checks is broken (try one: e.g. make `_serving` send a GET to `/` and see the slow-page test fail)
- the file passes on 16 workers (`-n 16`) three runs in a row
- all gates pass (see `docs/workflow.md`)

```yaml
# --- runner ---
result: done
attempts: 1
duration_s: 2770
gate_failures: []
tokens: 1282220
```
