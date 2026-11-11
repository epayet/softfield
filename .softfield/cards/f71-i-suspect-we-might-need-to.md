# Milestone F71: I suspect we might need to increase the timeouts as the…

> **State:** ready · **Priority:** 11 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
I suspect we might need to increase the timeouts as the tests take quite some time. i see dev tasks that are taking almost 45 minutes to complete, but do manage to complete, what would be a good value

(2026-10-09) make a separate investigation on the slow tests and suggested steps. they still need to be quite thorough for the less capable developers but they seem like a big bottleneck atm

### From F168: The full test suite takes 19 minutes and grows each day:… (merged by the lead on 2026-10-21)
The full test suite takes 19 minutes and grows each day: find the slowest tests (tests/factory_dashboard/test_app.py takes 3 s a test) and make them faster

### From F221: Tests are back to being slow again, probably some clock… (merged by the lead on 2026-11-05)
Tests are back to being slow again, probably some clock related tests. Plan to improve test speed, we already run them in parallel they used to take about 4 minutes

## What we know (2026-10-09)
- A developer attempt is already cut off at 45 min (`[timeouts] opencode = 2700` in `.softfield/project.toml`, raised from 30 in M4 when 8 of m4-06's 9 attempts hit it). An attempt that finishes at "almost 45 min" finishes just under the cut: the next slightly bigger one is lost.
- `check-all` takes 5–10 min (ADR 23), and a developer runs it at least once, often two or three times. Tests are a third or more of an attempt.
- Most timeouts in the session reports were attempts going nowhere (F6's page tickets, f8-06 attempt 3): a longer cut doesn't save those, and the 10-minute no-edit stop already catches the stuck ones early.
- Claude's jobs (lead tickets, escalations that implement, directions, checkpoints) share one 30-minute cut (`claude = 1800`) and run `check-all` too, once or twice: 10–20 of their 30 minutes. No session report shows one cut off yet, but the margin shrinks as the suite grows, and a Claude job cut off loses everything it spent.
- One ticket runs the whole suite four or five times: the developer's `check-all` (2–3 times), the `all-tests` gate (`runner/gates.py`, the same files again), `tests-fail-on-main`, then the merge's `check-all` (ADR 23). Every run is serial: no `pytest-xdist` in `pyproject.toml`, browser tests included.

## Decisions
- **D1: developer attempts get 60 minutes** (`opencode = 3600`). Not more: a ticket that fails three times would hold the GPU and the queue for 3 h instead of 2 h 15; 60 gives the attempts that now finish at 40–45 min a third more room.
- **D2: Claude's jobs get 45 minutes** (`claude = 2700`), the owner's point (2026-10-09). A longer cut costs nothing unless a job needs it; reviews stay at 3600. `gate` and the shell timeout (900 s, above a 10-minute `check-all`) stay.
- **D3: an investigation of the slow tests, as its own ticket** (f71-02, the owner's request). It keeps every test: the developers need the suite thorough. It measures first, then proposes:
  - where the time goes: per directory and the 30 slowest tests (`pytest --durations`), browser tests' share, `mypy`'s;
  - running the suite in parallel (`pytest-xdist`), and whether the tests are ready for it (database per worker, live-server ports, Playwright);
  - running the same tree once: the `all-tests` gate repeats a `check-all` that just passed on the same files;
  - what a developer runs while working (its ticket's tests and their neighbours) against at the finish (`check-all`, unchanged);
  - slow fixtures that could be shared (a browser or server per session, not per test).
  
  Its result is a findings section on this card, with each step's measured or estimated saving in minutes per ticket, then tickets in `.softfield/tasks/later/` and, for a gate change (a workflow rule), a draft ADR. Nothing is changed by the investigation itself.
- **D4: no later look** (owner, 2026-10-10: the periodic factory review, F59, covers that). f71-02's report says now, from the jobs already in the metrics database, how long developer attempts and Claude jobs take and how many were cut off, and whether D1's and D2's values fit; anything to change is an immediate follow-up for the owner to approve.

## What we saw on 2026-10-13 (f19-01, a terminal session with the owner)
- **A passing attempt ended at minute 57 of 60, and another was cut at 59.** f19-01's third attempt wrote its change and had its own tests green in 22 minutes; the other 35 went to three `check-all` runs: one killed at 600 s (a limit the model set itself; its output was "(no output)"), one of 12.5 min that failed on a single unused variable (`ruff` finds it in a second, but `check-all` reports only at the end), one of 12.5 min that passed. Its first attempt was cut at 59 min with 34 min in `check-all` the same way.
- **The suite now takes 750 s** against a gate and shell limit of 900 s.
- **The owner stopped the runner 13 minutes into the gates,** reading "70 minutes" as a broken 60-minute limit: the limit covers the developer's work, and the gates ran after it. A restart would have counted the finished attempt as timed out and run the developer again.

## Decisions (2026-10-13)
- **D5: developer attempts get 75 minutes** (`opencode = 4500`), and the gate and the developer's shell get 20 (`gate = 1200`, `SHELL_TIMEOUT_ENV`). The third raise for one cause, the suite's length: f71-02 goes at the cause.
- **D6: a stop during the gates runs the gates again, not the developer** (`_recover` and `_regate` in `runner/loop.py`, done in the session): the attempt's own commit at the tip of a clean branch means it had finished.
- **D7: the developer keeps `check-all` as its finish line** (owner: without the full suite it can't know its change works; f19-01 changed `base.html`, which every page's tests load). What a run costs is f71-02's subject, with two steps added to its list: the quick checks first, telling the developer at once when one fails, each result printed as it finishes; and the developer's prompt saying not to set a time limit on `check-all`.

## Decisions (2026-10-16)
- **D8: Claude's jobs get 75 minutes** (`claude = 4500`, the developer's D5), the owner's call after f17-01. Escalations and lead tickets already share this one limit. f17-01's escalation built the whole ticket, ran check-all, fixed a mypy error and was cut at 45 minutes while waiting on its second check-all, after writing its decision. Reviews stay at 3600.

## Findings (2026-10-21, f71-02, a terminal session with the owner)
Found because `check-all` timed out at its 1,200 s limit that night, with every test passing.
- **The suite took 19.6 minutes in one process** (1,177 s, 2,468 tests) on a 24-core machine: the gate limit is 20 minutes. By file: `test_app.py` 338 s (98 tests, 3.5 s each), `test_planning.py` 168 s, `test_loop.py` 151 s, `test_line.py` 115 s, `test_overview.py` 105 s; the rest under 65 s each. `mypy`, `ruff` and the layout check are seconds.
- **The browser tests are 6% of the tests and 40% of the time** (152 tests, 468 s). They wait on the pages' real 5 s polls, eight notification tests first wait 12 s for something that never comes before their fallback (17.5 s each), and one test backfills a database from this repo's runs to get one page (28 s, and it leaves a file in `/tmp`).
- **The tests are ready to run in parallel:** each uses its own `tmp_path`, none opens a real port, and Playwright serves pages from disk. With `pytest-xdist`, everything passed: 6.5 min on 8 workers and 4.9 min on 16 (load average under 9, so the slow waits set the pace, not the CPU). `check-all` with 16 workers: **4.5 min, all checks OK.**
- **Full suite runs per developer ticket:** the developer's own `check-all` (2–3 per attempt) and the `all-tests` gate. Lead tickets and escalations add one `check-all` before their merge. At 19.5 min a run, check-all was 40–60 of a 75-minute attempt; at 4.5 min it is 10–15.
- **Jobs over the last two weeks** (`softfield look`, from 2026-10-07): 257 developer attempts, 36 cut off (14%); 13 of the 82 attempts that passed since 2026-10-13 ran over 75 min, gates included. Claude's jobs: none cut off; the longest was a lead ticket at 66.5 min (limit 75), escalations at most 45, reviews 46.6 (limit 60).

### Verdicts
| Step | Verdict | Saving per ticket | Risk |
|---|---|---|---|
| Run the suite in parallel (`pytest-xdist`, 16 workers) | **Done** in the session: `[checks] test_workers` in `.softfield/project.toml`, used by `check-all` and the `all-tests` gate. Other projects keep 0 (one process) until their dev dependencies have `pytest-xdist` | 15 min per suite run: 45–60 min per developer ticket (3–4 runs), 15–30 per lead ticket | A test sharing state across workers would fail at random. All 2,468 passed three times on workers; f71-03 asks for three runs in a row |
| Browser tests on a fake clock, not real 5 s polls | **Do**: f71-03 (lead, after f68-07 and f114-08/09/10, which rewrite the same tests) | 1–2 min per suite run on workers (the slowest tests set the pace) | A test whose meaning changes. f71-03 has each test fail on purpose once |
| Run the same tree once (drop the `all-tests` gate after a developer's `check-all`) | **Don't**: the developer's run is its own word, not proven to be on the final tree; the gate is the runner's own run, and now 4.5 min | 4.5 min | — |
| What a developer runs while working: its tests first, `check-all` at the finish | **Already so** (`.softfield/developer.md`, D7) | — | — |
| Shared slow fixtures (one browser or server per session) | **Don't**: pytest-playwright already shares the browser per worker; a page per test keeps tests apart | under 1 min | Tests leaking into each other |
| Quick checks first, answering at once when one fails | **Later**: with the suite at 4.5 min, a `ruff` slip costs 4.5 min, not 12.5. Look again if the suite grows past 10 | up to 4 min, when one fails | A developer fixing lint, then waiting on a second run for the tests |
| The developer's prompt sets no time limit on `check-all` | **Already so** (`.softfield/developer.md` item 14, from f109-03); its "about 12 minutes" now says 5 | — | — |

### The limits (D4, and F148's question)
- **Keep them all.** Developer attempts at 75 min, Claude's jobs at 75 and reviews at 60 fit: no Claude job was cut off, and the developers' cuts came from check-all eating 40–60 of their 75 minutes. With the suite 15 minutes shorter per run, a developer attempt gets 30–45 minutes back, more than any raise did. F148's answer: no bigger limit; the suite was the cause.
- **The gate limit (`gate = 1200`) stays:** the suite on workers takes a quarter of it. Watch it from the jobs table at the periodic factory review (F59, F150).

## What we saw on 2026-11-05 (F221, merged here: "back to being slow")
- **The whole suite on workers grew a little:** the `all-tests` gate averaged 218 s on 10-23 and 247 s on 11-04, 303 s at most.
- **The two gates around it run in one process** (`gate_task_tests`, `gate_tests_fail_on_main`): `test_board.py` alone takes 85 s and `test_overview.py` 122 s. On 11-04, `task-tests` averaged 194 s (414 s at most) and `tests-fail-on-main` 142 s (297 s at most; 505 s on 10-28). A passing developer attempt's three test gates took 387 s on 10-22 and 583 s on 11-04, and up to 728 s on 10-28.
- **`tests-fail-on-main` runs every changed test file to the end,** though one failure already gives its answer.
- **Real-time waits are still there:** f71-03 had waited for its place at the card's priority 100 since all its dependencies finished. `test_app.py` has nine `wait_for_timeout(6_000)` and `test_overview.py` one, and the pages' 5 s polls are waited on with `timeout=REFRESH` (12 s) in about 90 places. `test_line.py` already uses the fake clock, in about 40 tests.
- **Not measured:** each test's own time. A planner job can't run pytest, so f71-03 measures first. The time zone fixture F187 added (`_utc_zone`) only sets an environment variable and is not the likely cause.

## Decisions (2026-11-05)
- **D9: the two gates use the workers too, and `tests-fail-on-main` stops at its first failure** (f71-04). The same tests give the same verdicts. Estimated: about 4 minutes off each passing attempt.
- **D10: f71-03 goes next,** after f71-04, widened to every file with real-time waits. The card keeps the place the owner gave it on the board (3).
- **Checked against main on 2026-11-09:** the gates (`runner/gates.py`) and the real-time waits in `test_app.py`, `test_overview.py`, `test_thread.py` and `test_planning.py` are unchanged; `test_board.py` gained F192's tests, with waits of 500 ms at most. The test gates still averaged 185 s (`task-tests`), 250 s (`all-tests`) and 151 s (`tests-fail-on-main`) on 11-06. `f71-04` is still free.
- **D11: no new gate.** `test-patterns` already refuses a new `wait_for_timeout` on a developer's branch. Watching the suite's length stays with the periodic factory review (F59).

## Tickets
| # | Id | Who | Difficulty | What |
|---|----|-----|------------|------|
| 01 | longer-attempts | lead | 1 | **Done on 2026-10-12** in a terminal session (commit `119a206`): `opencode = 3600`, `claude = 2700`. No ticket left |
| 02 | slow-tests-study | lead | 4 | **Done on 2026-10-21** in a terminal session: Findings above; the suite runs on 16 workers |
| 04 | test-gates-on-workers | lead | 2 | D9: `task-tests` and `tests-fail-on-main` on the workers; the second stops at its first failure |
| 03 | browser-tests-on-a-fake-clock | lead | 5 | D10: the browser tests on Playwright's fake clock, measured before and after. After 04 |
