---
id: f4-36-fix-reserve-pill-test-deleted
milestone: f4-always-on
difficulty: 2
depends_on: []
files:
- tests/factory_dashboard/test_overview.py
tests:
- tests/factory_dashboard/test_overview.py
finding: f4-always-on-C11-1
---

### Goal
Fix a checkpoint finding on f4-25-fix-cached-tokens-are-hidden: its test change deleted `test_a_run_on_the_reserve_has_the_pill` and the summed-tokens test, so nothing checks those two screens any more.

### Context
The merge of `tasks/done/f4-25-fix-cached-tokens-are-hidden.md` replaced, in `tests/factory_dashboard/test_overview.py`:
- `test_a_run_on_the_reserve_has_the_pill`, which asserted that the "now" section of `/live` says "on Claude's reserve" for `serve_between(activity="gates · f1-21", reserve=True)`. `factory_dashboard/templates/_partials/running.html` still prints that pill for `job.reserve` and `run.reserve`; the only remaining test that mentions it asserts its absence (after a Ctrl-C).
- the nested `test_claude_job_shows_cached_and_turns` (tokens_in=36_000, tokens_cached=970_000, steps=18, expecting "read 970k tokens · 18 turns"), by a new test with only `tokens_in=None, tokens_cached=500_000`. The sum of uncached and cached input is no longer tested.

`tasks/ready/f4-26-fix-the-cached-token-regression.md` asks for the nested test to be collected; this ticket supersedes it for that part.

### Done when
- a test shows "on Claude's reserve" in the "now" section when the run is on the reserve (restored `test_a_run_on_the_reserve_has_the_pill`)
- a collected, top-level test shows "read 970k tokens · 18 turns" for tokens_in=36_000, tokens_cached=970_000, steps=18, next to the cached-only test
- the listed `tests:` pass, and fail without the change
- all gates pass
