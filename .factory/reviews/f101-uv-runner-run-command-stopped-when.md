# Review: F101, the runner waits instead of ending when it has nothing to run

- **Status:** done, signed off by the owner on 2026-10-15.

## Sign-off sheet

**Expected:** `uv run runner run` ends only when you end it. With nothing it can run, it stays up, says what it waits for, applies every request from the dashboard as it comes, and starts again by itself when work appears or Claude comes back.
**Done when:** with every ticket waiting for Claude's reserve, the run doesn't end and says "Idle: 22 tickets wait for Claude's reserve · the week resets Mon 17:00" on the console and in Now; the reserve switch, the week's reset, or an approved plan starts work with no terminal; what waits on you is named once; `--once` and Ctrl-C end the run, with a session report.

### 1. What changed
- The runner no longer stops when it has nothing to run. It holds, and every 5 seconds it applies what you asked from the dashboard, checks the backup and looks for work again.
- It says why it holds, once, and again only when the reason changes: "Idle: 22 tickets wait for Claude's reserve · the week resets Mon 17:00", "Idle: nothing is ready", "… · waiting for you: 1 sign-off, 2 blocked tickets".
- Turning the reserve switch on, the week's reset, or approving a plan starts the next ticket by itself.
- Ctrl-C ends it and writes the session report. A run left up for days writes one report per day it worked, at the first quiet moment after midnight, and none for a day with no work.
- New in this review: a Ctrl-C that fell between two 5-second polls ended with an error and no report; it now ends the same way as any other.
- **Not right yet:** the dashboard puts "Running:" in front of the idle line, in green ("Running: Idle: 22 tickets wait…"), in the top bar and in Now. f101-02 fixes that.

### 2. How to test it yourself
1. Start `uv run runner run` in a terminal while Claude is at its reserve with the switch off (or with nothing in the ready folder). It stays up and prints one "Idle: …" line.
2. On your phone, open the Overview: Now shows the same line (with "Running:" before it until f101-02 merges).
3. Turn on the week's reserve switch from the dashboard: within a few seconds the terminal shows your request and the next ticket starts.
4. With an empty queue, approve a plan from the desk: its first ticket starts by itself.
5. Leave it idle a few minutes: the idle line isn't printed again.
6. Press Ctrl-C while it is idle: it prints "Ended by you." and, if it merged anything, the session report's path.

I couldn't run the real runner or open the dashboard from this job. The steps above are each covered by a test on a small repo with a scripted clock.

### 3. Left for later
- **f101-02** (ready, a developer ticket): the dashboard shows the idle line as it is, without "Running:" and not in green. It holds the sign-off.
- **bug-02** (ready, a lead ticket, priority 5): while the runner sleeps for a Claude limit that has a reset time (the 5-hour window, or a week Claude refused), it still applies nothing from the dashboard until the reset, up to hours. F101 fixed the wait that had no end; this one is the same deafness in the wait that has one. It doesn't hold the sign-off.
- Backlog (F4): an idle runner restarts within seconds of any save under `runner/`, even half-way through a change in a terminal session.

### 4. Decisions waiting for you
None. The one point the plan left for you to weigh (a run that never ends keeps a terminal busy and the model loaded) was in the plan, with the hold as its recommendation, and the hold is what was built.

### 5. How the work went
- 2026-10-10: you planted the note after the run ended in 2.9 minutes with 22 tickets at the reserve. 2026-10-12: second note in a terminal session; answered from the code and planned as one lead ticket.
- 2026-10-13 11:59 ([session](../sessions/2026-10-13-1159.md)): f101-01 built by the lead in a headless job, merged first time in 40.9 minutes. No local tokens: `runner/` is protected. The run then restarted itself onto the new code, as it should after a runner change.
- 2026-10-13: this review, round 1. One fix by the review, one developer ticket, one bug ticket, one backlog line.
- Lessons:
  - The ticket's tests read the idle line from the database, where it was right, and nothing looked at the page that shows it. A Done when that names a page ("the Overview's Now says…") needs a test on that page, or a ticket for it. The plan had neither.
  - The plan fixed the place the run returned and left the place it sleeps. Both made the runner deaf to you; only the first was in your note. When a card says "the runner did nothing while I asked", look for every wait, not the one in the report.
  - A hold made of a 5-second sleep and a few hundredths of a second of work still has the work: what is caught around the sleep is missed around the rest.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - bug-02 soon: with it, the runner answers the dashboard in every wait it has, which is what steering from the planning room needs.
  - Now that the runner stays up, starting it is the only thing left that needs a terminal. A "the runner is stopped" item on the desk already exists as the top bar's "Stopped"; a way to start it without a terminal would need a system service, which is yours to decide and which the plan advised against. Worth an ADR only if the runner keeps stopping by itself.
  - The idle line is the first place that says in one sentence why nothing moves. The line's page could show it on the machine that waits, later.

### 7. What clogged the factory line
- **Two days with the runner stopped** (2026-10-10 19:13 to 2026-10-12): the bug this milestone fixes. Nothing you asked from the dashboard was applied and the week's reset on the 12th at 17:00 went unused. Unclogged by f101-01.
- **Three days from the note to the fix**: planted on the 10th, planned on the 12th, built on the 13th. The card was priority 1, but the runner that would have planned it was the one that had stopped.
- **The review:** one run of the three test folders, 3 min 40, twice. Nothing waited on a limit.
- I couldn't read hours from the metrics database in this job (a headless review has no query command); the figures are from the session report, the milestone doc and git. The fix is in the backlog (f53-review: a "where the hours went" block in `runner report`).

## What was built
- **The hold** (`runner/loop.py`, `work_queue`): where the standing command used to return with nothing to run, it now logs and shows an idle line and waits one poll (`_idle_holds`, 5 seconds), then takes the loop's next turn: the owner's requests, the backup, Claude's windows, the pick. Only under `reviews=True` without `once`, so `runner milestone` and `--once` end as before. The hold starts no job itself.
- **The idle line** (`_idle_line`): tickets parked for Claude with the earliest reset, tickets behind a blocked or escalated one, tickets waiting for a sign-off, and the open owner items by kind, the two switches' items left out since their tickets are counted already. Logged and written as the run's activity only when it changes.
- **The day's report** (`_idle_holds`, `SessionReport.idle`, `runner/cli.py`): an idle run with work to report closes its session at the first poll of a new day; the command opens the next. A run with nothing to report keeps one session.
- **Ctrl-C** while idle: "Ended by you.", the notes and the session report, as a normal end.
- **`docs/workflow.md`:** a paragraph on the standing command.
- **Tests:** ten in `tests/runner/test_loop.py`, one in `tests/runner/test_cli.py`, and a fixture in `tests/runner/conftest.py` that ends every other test's run at its first idle poll.

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | Ctrl-C was caught only inside the poll's sleep. Each turn of the hold also reads the runner's code, the requests, the backup, the tickets and the queue; a Ctrl-C landing there left `work_queue` as an error: no "Ended by you.", no session report for work already merged, the run closed as "interrupted" | Fixed: `run_session` ends the run the same way when the interrupt comes while the run shows its idle line, and lets it through otherwise. Two tests: between two polls (report written), and mid-work (still an interrupt) |
| F2 | should-fix | local | The dashboard prefixes any activity with "Running:" and paints it green (`factory_status` in `factory_dashboard/app.py`, `_partials/running.html`), so the idle run reads "Running: Idle: 22 tickets wait for Claude's reserve…". The Done when names Now's words; plain words and no unexplained colour are the owner's rules | `tasks/ready/f101-02-idle-reads-idle.md`, a developer ticket with the pause's branch and the top bar's test as examples |
| F3 | should-fix | backlog | `_wait_for_reset` still sleeps to a limit's reset in one `time.sleep` (up to hours), applying no request; only the 5-hour switch is read, for work held by the owner's share. The standing runner is up and deaf there, against the expected outcome. Code F101 didn't touch, and its D1 scoped the fix to the return. `_idle_line`'s "for Claude until …" branch can't be reached because of it, and has no test | Too important for a backlog line: `tasks/ready/bug-02-limit-wait-takes-requests.md`, priority 5, a lead ticket (protected code). It says what to keep: one `wait` usage event, the activity and its time |
| F4 | should-fix | backlog | An idle run reads `runner/`'s fingerprint every 5 seconds, so it restarts within seconds of any save there, committed or not; a terminal session half-way through a change can restart it onto code that doesn't import | `docs/backlog.md`, with the fix: while idle, restart only when `runner/` is clean in git |

Read and found sound, no finding:
- **No Claude from the hold.** The hold only sleeps; jobs start through `dispatch.pick` as before. The first test asserts no lead job ran over three polls and two days.
- **The heartbeat** is a thread of its own, so an idle run stays "live" for the dashboard and for `live_run`, which keeps `runner queue` from committing beside it.
- **Midnight** is local time (`now()`), compared with the session's start; a session with no ticket and no Claude run is never closed for it, so no empty report. The CLI test checks the command goes on after an idle session and ends after a plain one.
- **A due review** still returns to the command; `_queue_due_review` runs each turn of the hold.
- **The owner item kinds** in `OWNER_WAITS` are all those written today (`runner/owner.py`, the planner's); an unknown kind shows by its own name.
- **The tests can fail.** Each hold test scripts the polls and fails with `pytest.fail` or a wrong count if the queue returns early or holds on; `test_once_and_a_milestones_queue_end…` fails if the hold spreads to `--once` or `runner milestone`.

Edited existing tests: none. The developer of this ticket was the lead; the new autouse fixture in `tests/runner/conftest.py` changes what every older test meets at the end of its queue (a Ctrl-C at the first idle poll), which keeps their asserts on the report's notes true: I checked that `Paused (dependency escalated)` and `Waiting:` notes are still written on that path.

No checkpoint ran (a lead ticket), so there are no checkpoint findings to judge. French: nothing to check, no user-facing string and no `coucou/locale/` file changed. Screenshots: no browser in this job. After the fix, `uv run pytest -q tests/unit tests/integration tests/runner` gave 1831 passed, 1 skipped; ruff and mypy are clean on `runner/loop.py`.

Score: 8/10. The hold is small, reuses the loop's own turn instead of a second loop, and its tests script time well. It lost points for the page nobody looked at (F2) and the interrupt window (F1).

Stop reason: none. f101-02 runs next, then round 2 reads it.

## Factory
- **The flow:** one headless lead job, merged first time; the run restarted onto its own new code and went on to this review. No stop for the owner, no park, no limit.
- **Models:** Claude Opus only; see the numbers below. No developer work, so "Known range" in `docs/agents/lead.md` has nothing new. f101-02 will be the first developer work on this card.
- **What to change:**
  - A lead ticket gets no checkpoint, so its review is its only reader (F41, F53, F55, F79 and F104 said the same). Here the review found two things a checkpoint reading the diff could have: worth a cheap checkpoint on lead tickets over some size, to try on the next one.
  - A Done when that names a page gets a test or a ticket on that page (lesson 1). One line for `docs/task-writing.md` at the next planning session.

## Workflow observations
- The session report's narrative was empty: the runner asks for one only when the config says so. The lessons above stand in for it.
- The review's two new tickets are one in the milestone (f101-02, which holds the sign-off) and one bug (bug-02, which doesn't): the split follows the Done when, which F101 meets but for the dashboard's wording.

<!-- runner report -->
<!-- /runner report -->
