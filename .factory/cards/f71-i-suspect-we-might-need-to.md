# Milestone F71: I suspect we might need to increase the timeouts as the…

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
I suspect we might need to increase the timeouts as the tests take quite some time. i see dev tasks that are taking almost 45 minutes to complete, but do manage to complete, what would be a good value

(2026-10-09) make a separate investigation on the slow tests and suggested steps. they still need to be quite thorough for the less capable developers but they seem like a big bottleneck atm

### From F168: The full test suite takes 19 minutes and grows each day:… (merged by the lead on 2026-10-21)
The full test suite takes 19 minutes and grows each day: find the slowest tests (tests/factory_dashboard/test_app.py takes 3 s a test) and make them faster

## What we know (2026-10-09)
- A developer attempt is already cut off at 45 min (`[timeouts] opencode = 2700` in `.factory/project.toml`, raised from 30 in M4 when 8 of m4-06's 9 attempts hit it). An attempt that finishes at "almost 45 min" finishes just under the cut: the next slightly bigger one is lost.
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
  
  Its result is a findings section on this card, with each step's measured or estimated saving in minutes per ticket, then tickets in `.factory/tasks/later/` and, for a gate change (a workflow rule), a draft ADR. Nothing is changed by the investigation itself.
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

## Tickets
| # | Id | Who | Difficulty | What |
|---|----|-----|------------|------|
| 01 | longer-attempts | lead | 1 | **Done on 2026-10-12** in a terminal session (commit `119a206`): `opencode = 3600`, `claude = 2700`. No ticket left |
| 02 | slow-tests-study | lead | 4 | D3: measure where the suite's time goes and propose steps that keep every test. Waits for f95-02 (`runner look`) to read the jobs table |
