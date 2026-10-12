# Milestone F71: I suspect we might need to increase the timeouts as the…

> **State:** ready · **Priority:** 100 · **Area:** factory
> Planted by the owner on 2026-10-09.

## Notes
I suspect we might need to increase the timeouts as the tests take quite some time. i see dev tasks that are taking almost 45 minutes to complete, but do manage to complete, what would be a good value

(2026-10-09) make a separate investigation on the slow tests and suggested steps. they still need to be quite thorough for the less capable developers but they seem like a big bottleneck atm

## What we know (2026-10-09)
- A developer attempt is already cut off at 45 min (`[timeouts] opencode = 2700` in `workflow/runner.toml`, raised from 30 in M4 when 8 of m4-06's 9 attempts hit it). An attempt that finishes at "almost 45 min" finishes just under the cut: the next slightly bigger one is lost.
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
  
  Its result is a findings section on this card, with each step's measured or estimated saving in minutes per ticket, then tickets in `tasks/later/` and, for a gate change (a workflow rule), a draft ADR. Nothing is changed by the investigation itself.
- **D4: no later look** (owner, 2026-10-10: the periodic factory review, F59, covers that). f71-02's report says now, from the jobs already in the metrics database, how long developer attempts and Claude jobs take and how many were cut off, and whether D1's and D2's values fit; anything to change is an immediate follow-up for the owner to approve.

## Tickets
| # | Id | Who | Difficulty | What |
|---|----|-----|------------|------|
| 01 | longer-attempts | lead | 1 | **Done on 2026-10-12** in a terminal session (commit `119a206`): `opencode = 3600`, `claude = 2700`. No ticket left |
| 02 | slow-tests-study | lead | 4 | D3: measure where the suite's time goes and propose steps that keep every test. Waits for f95-02 (`runner look`) to read the jobs table |
