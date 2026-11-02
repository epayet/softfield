# Review: F28, Pause and Resume hold what you asked through the refresh

- **Status:** done, signed off by the owner on 2026-10-21.

## Sign-off sheet

**Expected:** Pause or Resume in the top bar shows what you asked at once and keeps showing it until the runner agrees; the 5 s refresh no longer puts the old words and the old button back. A request that doesn't reach the dashboard's server says so, and the button comes back. Overview's Now says the same as the top bar, "Resuming…" included (F29), and the top bar is the one Pause/Resume button.
**Done when:** on a phone, press Pause while a job runs: "Pausing after this job" shows at once and stays, never flicking back to Pause; then Resume: "Resuming…" stays until the runner resumes. Overview's Now says the same as the top bar at every step, and has no button of its own.

### 1. What changed
- **Pause sticks the first time.** Press ⏸ in the top bar: it reads "Pausing after <the ticket>" with the dashed orange edge, and a refresh that left before your press can't bring "Running" and ⏸ back. The bar changes again only when the runner's own state does.
- **Resume sticks too.** Press ▶: "Resuming…" stays until the runner picks it up, then the bar shows what runs.
- **A failed press says so.** If the press doesn't reach the dashboard's server, the bar reads "Didn't reach the factory: try again", and the next refresh brings the button back.
- **Now has no button of its own.** Overview's Now shows the pause in the top bar's own words, "Pausing after…", "Paused by you since…", "· the lead is answering you" or "Resuming…", and the top bar is where you press.

### 2. How to test it yourself
1. On the phone, open any page while a ticket runs and press ⏸. "Pausing after <ticket>" shows at once. Watch for 15 seconds: it never goes back to "Running" or shows ⏸ again.
2. When the job ends, the bar reads "Paused by you since HH:MM" with ▶.
3. Open the Overview: Now's line reads the same words as the bar, and Now has no Pause or Resume button.
4. Press ▶: "Resuming…" stays, on the bar and on Now, until the runner picks the next ticket.
5. To see the failure words: stop the dashboard (Ctrl-C) with a page still open on the phone, press the sign; the bar reads "Didn't reach the factory: try again". Start the dashboard again and the button comes back within a refresh.

I couldn't open the real dashboard from this job; each step is covered by a browser test on the fixture database, and the stale-refresh tests now fail if the fix is taken out.

### 3. Left for later
Nothing new. F17 restyles the one button later, as the card said.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-07: you planted F28; F29 and F34 (the same root) merged into it on 2026-10-08. Planned as two developer tickets.
- 2026-10-15 00:23 ([session](../sessions/2026-10-15-0023.md)): f28-01 merged on its third attempt after a direction (a no-edit stop, then a timeout), 122 minutes of model, 13.1M local tokens. The checkpoint passed it.
- 2026-10-15 06:31 ([session](../sessions/2026-10-15-0631.md)): f28-02 escalated after three attempts; the lead built it. The review then stopped on "end-to-end tests fail on staging" (a project with none).
- 2026-10-21: this review, round 1, after f135-01 fixed that stop. Four fixes by the review, no ticket.
- Lessons:
  - **A ticket that breaks a protected test is the lead's.** f28-02 asked to remove Now's buttons, which the protected `test_requests.py` asserted; no attempt could pass. Now in `docs/task-writing.md`: grep the protected tests for what a ticket removes before queueing.
  - **A test of a race must look inside the race.** f28-01's tests served a stale refresh and then a fresh one, but only checked the end; without the fix, the stale one showed for 5 seconds and the tests still passed. The checkpoint read them and called them sound. The review made them check right after the stale refresh, and proved they fail without the fix.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - "Fail without the change" is in every ticket and nobody checks it test by test: the `tests-fail-on-main` gate runs the changed test files on main's code and passes when any one test in them fails (here the refused-post test did, and carried the two hollow ones). Worth a planted card:
    > Gate: each new test a developer adds must fail on main without the change, not just one of them; name the ones that pass anyway in the gate's message.
  - Script-and-template tickets on the top bar and Now keep costing the developer two hours for 50 lines (F19, F28): the routing rule from F14/F30 should send them to the lead.

### 7. What clogged the factory line
- **Eight days from the note to the first merge** (planted 2026-10-07, f28-01 merged 2026-10-15): the queue's order, and both tickets held behind f12-03 (the red main of 2026-10-10).
- **Failed attempts:** f28-01, two failed attempts (a no-edit stop, a timeout) and about 2 hours 20 minutes of model and gates for 48 lines of script. f28-02, three attempts and a direction that could never pass (the protected test), about an hour, then the escalation. Unclog: the protected-test grep at planning (done), and the lead takes top-bar script tickets.
- **A review that stopped on nothing:** the first review stopped at once with "end-to-end tests fail on staging"; f135-01 fixed it, and this is the rerun, six days later.
- I couldn't query the metrics database from this job; the hours are from the session reports and the commit trailers.

## What was built
- **f28-01** (`base.html`): the top bar's script remembers the kind just asked; on `htmx:oobBeforeSwap` a refreshed bar that still offers that kind is kept out, and the first one that differs is swapped in and clears the memory. A refused or unsent post shows "Didn't reach the factory: try again" and clears it. Three browser tests.
- **f28-02** (by the lead, after the escalation; `overview.py`, `running.html`): `pause_words` takes the top bar's own `factory_status` words when they are a pause, so Now can't drift from the bar; both of Now's buttons are gone. The protected pause tests assert Now's line equals the bar's words and that Now has no button.
- **The review** (`base.html`, `overview.py`, `test_app.py`): the stale-refresh tests check inside the race (F1), a test that Now matches the bar for every pause state (F2), and two tidy-ups (F3, F4).

## Findings and resolutions
| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | f28-01's two stale-refresh tests checked only the state after the fresh refresh (within two polls), so they passed without the fix: the milestone's own bug had no guard | Fixed: a page listener counts the refreshed bars after `base.html` has judged each one; once the stale bar has arrived, the tests assert the asked words, the dashed edge and no sign. With the guard line disabled both fail on the stale bar; restored, both pass |
| F2 | should-fix | claude | No test that Now reads "· the lead is answering you" while paused with a planner job (F34 named it), nor that Now equals the bar for every pause state | Fixed: `test_now_says_the_pause_in_the_top_bars_words_without_a_button`, over the four pause setups of the top-bar test |
| F3 | nit | claude | `base.html` kept two variables nothing read and repeated a three-line reset three times | Fixed: one `askedKind`; the swap handler is four lines. A bar whose `hx-vals` doesn't parse now clears the memory instead of keeping it |
| F4 | nit | claude | `overview.pause_words` imported `factory_status` inside the function, though `overview` already imports `app` at the top | Fixed: it joins the top import |

Checkpoint findings: none were raised. Missed by the checkpoint: F1 (checkpoint 2 of 2026-10-15 read f28-01's tests and called them sound).

Read and found sound, no finding:
- **The swap rule** covers every state: a pause's stale bar offers ⏸ (kept out), the runner's "Pausing after…" offers ▶ (swapped in); a resume's stale bar offers ▶ (kept out), "Resuming…" offers nothing (swapped in).
- **The failure listeners sit on the button itself,** since the button leaves the page before the answer; the refused-post test proves they fire.
- **Edited existing tests.** f28-01 only added tests. The escalation rewrote `test_requests.py`'s four pause tests for Now with no button: honest, each still checks the request row and Now's words.
- **Now with the runner stopped** shows no pause line, as the bar shows "Stopped": the card asks for the same words in both.

Checks: `uv run pytest -q tests/runner tests/factory_dashboard` ran green to 93% before this job's 20-minute limit stopped it, with no failure; the rest of the dashboard files then ran on their own and passed (`test_app.py` 98, `test_overview.py` and `test_requests.py` 178, the last five files 91). Ruff is clean on both edited Python files.

French: nothing to check, no `coucou/locale/` file changed. Screenshots: no browser of my own in this job; the browser tests drove Chromium.

Score: 7/10. The design is small and right (no server change, one rule for both kinds) and Now can no longer disagree with the bar. It lost points for tests that didn't guard the bug they were written for, and a ticket that couldn't pass as written.

Stop reason: none.

## Factory
- **The flow:** two developer tickets, one direction, one escalation (the lead's ticket at fault), one checkpoint with no findings and one miss. No stop for you during the build; the first review stopped on the staging rule (fixed by f135-01).
- **Models:** Qwen 0/2 first time, 13.4M tokens. Claude: the checkpoint on Sonnet, the escalation and this review on Opus; see the numbers below.
- **What to change:**
  - A per-test "fails on main" gate (card text above, for you to plant).
  - Checkpoint brief: for a test of a race or a refresh, check it asserts while the stale state would show, not only the end state. A one-line addition, for the next planning session.

## Workflow observations
- The milestone's start tag predates other cards' work, so `git diff …-start..main` covered 356 files; the review read the f28 commits (628e70d, 698b87d) instead, as F19's did.

<!-- runner report -->
<!-- /runner report -->
