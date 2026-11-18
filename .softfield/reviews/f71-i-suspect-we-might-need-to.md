# Review: F71, the slow tests (round 1, 2026-11-18)

## Sign-off sheet

### 1. What changed
Nothing on any page: this card is about how long the tests take.
- **The runner's test gates use the workers too.** `task-tests` and `tests-fail-on-main` now run on the project's 16 workers like `all-tests`, and `tests-fail-on-main` stops at its first failure (one is enough for its answer). On 11-04 these two gates took 3–7 minutes per passing developer attempt. No developer attempt has run since, so the saving isn't measured yet.
- **The dashboard's browser tests run on a fake clock.** They no longer sit through the pages' real 5-second polls. The slowest test went from 36 s to under 4 s, and no dashboard browser test now takes more than 3.8 s. The whole `check-all` went from 271 s to 246 s. On 16 workers, what sets the suite's length now is its 3,600 tests, not its waits.

### 2. How to test it yourself
1. On the dashboard's Jobs page, open the next developer attempt that passes. In its gates, `task-tests` and `tests-fail-on-main` should each take well under a minute (on 11-04 they averaged 194 s and 142 s).
2. On the same page, the next `check-all` or `all-tests` should take about 4 minutes, not 5.
3. Nothing to check on a phone: no page changed.

### 3. Left for later
- Two slow tests outside this card's files: see the Factory quotes in item 6.
- Two "nothing was re-fetched" checks still wait a fixed 300 ms: see item 6.

### 4. Decisions waiting for you
None.

### 5. How the work went
- **2026-11-18 16:06** ([session](../sessions/2026-11-18-1606.md)): f71-04 merged on its first attempt, a Sonnet lead ticket, in 10 minutes for $0.20. The runner then stopped for a fresh process because `runner/` had changed.
- **2026-11-18 16:21** ([session](../sessions/2026-11-18-1621.md)): f71-03 merged on its first attempt, an Opus lead ticket. Its first 13 minutes were lost to Claude's 5-hour limit; it resumed at 17:10 and finished in 39 minutes, for $6.86.
- No local model work: both tickets touch protected code or many test files at once.

What the work taught:
- **The fake clock fixed the slowest tests but not the length of the suite.** On 16 workers, the time follows the number of tests, so the next large saving won't come from waits. That makes the periodic factory review the right place to watch the suite's length (D11), not another card.
- **A test that proves "nothing happened" can pass for a reason it never names.** The thread test's 5-second wait fell inside the page's 10-second scroll hold, so it never tested the typing hold its name promises. The review found this by breaking that one rule. The ticket's own mutations had broken the whole hold at once.
- **A Done-when line asking for one exact command** (a serial run over 10 minutes) couldn't fit a job that must run everything in the foreground. The 16-worker run answered the same question.

### 6. What next
- **Product:** nothing; this card is factory work.
- **Factory:**
  - The tail of the suite is now two tests outside this card's files:
    > tests/factory_dashboard/test_jobs.py's test_more_than_200_jobs_shows_200_and_count spends 13 s in setup writing 200 jobs one at a time: write them in one transaction so it takes under a second.

    > tests/runner/test_shots.py waits on the real page-readiness timeouts (12.5 s in test_a_slow_page_gets_its_pictures_and_no_readiness_request, about 5 s in three more): make those timeouts a parameter the tests set to a fraction of a second.
  - Two checks still guess with a fixed wait:
    > test_a_change_that_isnt_stored_leaves_the_row_open (test_coming.py) and test_a_message_change_that_isnt_stored_leaves_the_editor_open (test_thread.py) still prove "no re-fetch followed" with wait_for_timeout(300): use watch_requests and requests_until from the dashboard tests' conftest, as f71-03 did for the other two.
  - Once a few developer attempts have run, check the test gates' times on the Jobs page against 11-04's (194 s and 142 s). The periodic factory review covers this; no card is needed.

### 7. What clogged the factory line
- **Claude's 5-hour limit: about 49 minutes.** f71-03's first job ran 13 minutes (16:21–16:34) before it was parked. The probe at 16:44 found the limit reached, resetting at 17:10, and the ticket resumed then. Most of that run's spend went to the planner, review and lead jobs earlier that day (jobs 2364–2404). What would help: the pace rule (ADR 50) already orders work under the limit, and a ticket this large (difficulty 5, Opus) could be picked right after a reset rather than at the end of a busy window.
- **The runner restart after f71-04: about 4 minutes** (16:17–16:21). A lead ticket that changes `runner/` needs a fresh process. It is small, and it is by design.
- No failed attempts, and the owner didn't step in.

---

## What was built
- **f71-04 (D9):** `worker_args()` in `runner/config.py` is shared by `suite_args()`, `gate_task_tests` and `gate_tests_fail_on_main` (`runner/gates.py`). `tests-fail-on-main` adds `-x`. Its tests cover both 4 workers and 0, and check that the branch is clean after an early stop.
- **f71-03 (D10):** `poll(page)` in `tests/factory_dashboard/conftest.py` runs the page's clock 5.1 s, waits until every htmx request it sent is answered, then runs 100 ms more for htmx's settle. `watch_requests` and `requests_until` record htmx's requests in order, for checks that something wasn't sent. Every `wait_for_timeout(6_000)` and every poll wait in the listed files now uses them. The thread page reads itself again with a plain `fetch`, so its tests run the clock and then wait for the redraw. The app's code is unchanged.

## Findings and resolutions
| Id | Grade | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | `test_an_open_thread_waits_while_the_owner_types` checked its "no read" inside the 10 s scroll hold that the fill starts, so it passed even with the typing hold removed | **Fixed by the review:** the test runs the clock past the scroll hold before its poll. With `liveIdle` cut after its scroll check (a temporary break, since undone), the new form fails with 1 read; the old one would have seen 0 at 5 s |
| F2 | nit | later | Two "no re-fetch followed" checks still wait a fixed 300 ms (`test_coming.py:1014`, `test_thread.py:1590`) | Quoted in item 6 |
| F3 | should-fix | later | The suite's slowest tests are now `test_jobs.py`'s 200-jobs setup (13.4 s) and `test_shots.py`'s real timeouts (12.5 s) | Quoted in item 6. f71-03's note named them too |
| F4 | nit | report | f71-03's serial `--durations` line was met with the 16-worker run (the serial run takes over 10 minutes, past the job's limit for one command) | Accepted: it answers the same question, and the review's run agrees |
| F5 | nit | report | The suite as a whole gained only 25 s (271 s to 246 s); it is now set by the number of tests | Said here only |

No checkpoint ran on this card: both tickets were lead tickets. The tests: 3,642 passed on 16 workers in 258 s (`uv run pytest -q -n 16 tests/runner tests/factory_dashboard`), with the review's fix. French: nothing changed in `coucou/locale/`. Score: 8.

## What was set aside
- Card D1–D8's timeout values: unchanged, as D4 and the 10-21 findings decided.
- The slow tests outside the ticket's files (F3): left for a card, as quoted above.

## Workflow observations
- f71-03's mutation table was the right check. It broke whole mechanisms, though: the hold, the poll. A test named after one rule ("while the owner types") needs that one rule broken. When a ticket asks for "every changed test still fails when the behaviour it checks is broken", the developer should break the rule the test's name states, not the feature around it. This lesson goes in the ADR 02 learnings log; it doesn't need a gate.
- f71-03 cost $6.86 for 75 turns, with 18M cached tokens re-read. Rewriting tests across seven files in one Opus job is expensive but safe. One ticket per file would have meant seven re-readings of the card and conftest. The cost was worth it.

<!-- runner report -->
<!-- /runner report -->
