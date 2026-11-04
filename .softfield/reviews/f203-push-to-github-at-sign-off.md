# Review: F203, a sign-off pushes the milestone to GitHub

- **Status:** done, signed off by the owner on 2026-11-04.

## Sign-off sheet

### 1. What changed
- **While the runner pushes, the top bar and the Overview say "Running: pushing to GitHub",** not "picking the next ticket". On 2 November the first catch-up sent 64 tags in about 2 minutes under the old words, and the runner looked as if it was doing nothing.
- **When there's nothing to push, the words never appear.** A pick with no new tag doesn't contact GitHub at all.
- Afterwards the bar goes back to what it said before.

### 2. How to test it yourself
1. Keep the dashboard open on your phone, on the Overview.
2. Sign off a milestone on its page.
3. At the runner's next pick, the top bar and the Overview's running section should say "Running: pushing to GitHub", then go back to what they said before.
4. Check that the milestone's tag is on GitHub.

One new tag takes seconds, so you may miss the words between two refreshes of the page. That isn't a fault. The test in `tests/runner/test_loop.py` shows the words are set for the whole of the push.

### 3. Left for later
Nothing new, and no bug ticket set aside. Two small points are only reported below, under Findings.

`bug-59-expired-login-waits` is already in the queue. It came from this ticket's run and is the fix for most of the lost time (see 7).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-04, the run started at 10:19: two lead-ticket attempts failed, Sonnet with 11 steps and then Opus. Claude's login expired during the first, so the ticket was blocked at 12:27 with "check-all failed". The lead's look at that block failed for the same reason. That run has no session report in `.softfield/sessions/`.
- 2026-11-04, 20:26, your terminal session: the lead finished the ticket from its branch and merged it as `95160d96`.
- 2026-11-04, 20:33: review round 1, no defects.
- Lessons:
  - **The code was never the problem.** It's a three-line change, and it took 10 hours because of an expired login. bug-59 makes the runner hold Claude's jobs and ask you to log in.
  - **The block's reason was misleading.** "check-all failed" described work that stopped when the login ran out, not code that was wrong. bug-59 stops a job from reaching that point.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** run bug-59 first, ahead of other Claude work: it cost this ticket and f162-01 most of a day, and it can happen on any night.
- **Factory:** when a run ends without closing properly, write its missing session report at the next start. I'd do that only if it happens again, since one missing report isn't worth a run yet.

### 7. What clogged the factory line
- **The expired login: about 3 hours of failed work (10:20 to 13:25).** Five jobs failed, each waiting through its retries for 16 to 26 minutes. Two of them were this ticket's attempts, and the rest were the two planner looks and f162-01. Each job's `claude` log holds "Failed to authenticate". bug-59 unclogs this.
- **Two gaps of 40 minutes with no job recorded:** 10:46 to 11:26 and 11:47 to 12:27. The metrics don't say what they were. They're probably the checks on the branch, but I haven't confirmed that. Nothing to unclog until they're known.
- **Waiting for a login: about 7 hours (13:25 to 20:26).** No run was live until 20:32, after your terminal session. Your desk showed two blocked tickets and "The lead couldn't look at the ticket blocked on F203", but none of the three items mentioned the login. bug-59's desk item and notification unclog this.

## What was built
`check_push` in `runner/loop.py` wraps `push.push_signed_off` in `doing(s, "pushing to GitHub")`. A new test, `test_the_activity_says_pushing_only_while_a_push_runs`, covers it.

**Tests:** no existing test was edited. The new test checks the activity from inside the real `push_signed_off`, so it fails without the change. It checks that the activity is restored afterwards, then runs a second pick with no new tag and shows the activity isn't set. The dashboard's side is the same `Running: <activity>` path that `test_overview.py` already tests with other words, so it needs no new test.

No French changed: this is the factory's dashboard, in English.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | nit | report | The words say "GitHub" for any `origin` | Not fixed: the ticket asked for these words, and `remote_of` gives only the name `origin`, which says less. If a project ever uses another host, take the name from the remote's address. |
| F2 | nit | report | A retry after a failed push shows the words with no new tag, which the Done when's wording doesn't allow | Not fixed: the code is right, since a retry does contact the remote, as the ticket's Context means. A fix would be wording in a closed ticket. |

What held up when I looked for trouble:
- **A failed or refused push:** `doing` restores the activity in its `finally`, and `check_push` handles the outcome after the block, so the bar doesn't say "pushing" during the desk-item writes.
- **Ctrl-C during an idle pick:** `doing` restores the idle line before the interrupt reaches `run_session`, whose handler looks for that line, so the run still ends as one Ctrl-C at idle should.
- **Waiting for Claude:** `doing` clears `waiting_until` for the block and puts it back, and `check_push` isn't called in that wait anyway.
- **The factory line page:** `line.py` skips an activity it doesn't know, so "pushing to GitHub" adds nothing there, as with the other activities that aren't waits. The ticket asked only for the bar and the Overview.

Checkpoints: none read this ticket, so there's nothing to judge and no "missed".

## What was set aside
F1 and F2, as above. No bug tickets: neither is worth a run.

## Workflow observations
- **Checks run in this review:** the three push tests in `tests/runner/test_loop.py` pass, and `ruff` passes on both changed files. I changed no code, so I didn't rerun the whole suite or `softfield check-all`.
- **The ticket was the right size:** its Context named the exact call to wrap, and the result is what it described.
- **The owner's session finished work the runner couldn't.** The ticket's result says `attempts: 3`, while the metrics hold two jobs: the third was the terminal session, which has no job row or cost. A finish like that won't show in the numbers below.
- `softfield report` isn't among the commands a review may run, so the numbers below come from the runner.
- The ADR 02 entry is added.

<!-- runner report -->
<!-- /runner report -->
