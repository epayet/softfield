# Review: F135, reviews stopped at once on end-to-end tests the split removed

- **Status:** round 1 done, clean, ready for your sign-off.

## Sign-off sheet

**Expected:** a Softfield milestone review goes straight to Claude's rounds; F28 and F19 get their review without you doing anything, and their two stops leave Needs you.
**Done when:** a review of a project with no end-to-end tests runs its rounds and says in its log that there were none to run; F28's and F19's reviews run again on the runner's own, and their review-stop items go once their verdict is written.

### 1. What changed
- **Reviews no longer stop on nothing.** The two "end-to-end tests fail on staging" items on Needs you (F28's and F19's) are gone. No test had failed: the review was looking for Coucou's browser tests, which moved out of this repo with the split.
- **F28 and F19 were reviewed by themselves.** The runner saw their old stops were stale and ran both reviews this morning (07:10 and 07:34), with no command from you. Both are now waiting for your sign-off.
- **Coucou is unchanged.** It still runs its browser tests before a review, and a real failure there still stops and asks you.

### 2. How to test it yourself
1. Open the Overview on your phone. Needs you no longer lists "end-to-end tests fail on staging" for F28 or F19.
2. Under sign-off, F19 and F28 each show their review sheet.
3. Open any run page of a review from today. Its log says "e2e tests skipped (no end-to-end tests in [checks])", then Claude's round.

### 3. Left for later
Nothing.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-10-15: you planted the question; F156 asked the same on 2026-10-20 and was merged into this card.
- 2026-10-15 09:15 (terminal session, commit 947dd8c): the lead made end-to-end tests run only where a project's `[checks]` names them (D1). The two stops already recorded were left as they were.
- 2026-10-21 06:10 ([session](../sessions/2026-10-21-0610.md)): f135-01 (lead ticket, protected `runner/`) merged on the first attempt: a stale end-to-end stop makes the review due again (D2). Two tests. 0 local tokens.
- 2026-10-21 07:10 and 07:34 ([F19](../sessions/2026-10-21-0710.md), [F28](../sessions/2026-10-21-0734.md)): the reruns this card asked for, both clean.
- Lessons:
  - **A fix should clear what the bug left behind.** On 10-15 the cause was fixed in minutes, but the two stops it had already recorded waited six more days for this ticket. When a fix removes a stop's cause, clear the stops it recorded in the same change.
  - **A hard-coded check left behind by a split.** ADR 30 moved every check into `[checks]` except the end-to-end run. The ticket's test shows the case is now covered.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Needs you could say what a stop means and whether it will clear by itself. F156 was you asking exactly that. Worth a planted card:
    > Needs you: each review stop says in plain words what happened, whether the runner will retry it by itself, and what I can do, so I don't have to ask.
  - When a terminal session fixes the cause of a stop, it also clears the stops already recorded: now a rule in `docs/agents/lead.md` ("A fix clears what the bug left behind"), no ticket needed.

### 7. What clogged the factory line
- **Six days of stale stops** (2026-10-15 to 2026-10-21): F28 and F19 sat on Needs you after their cause was fixed, because the stop in `state.json` counted as "reviewed". To unclog: clear recorded stops along with their cause, as above.
- **One runner restart:** f135-01 changed `runner/`, so the runner stopped for a fresh process after it. That is expected for protected code.
- I couldn't query the metrics database from this job; the hours are from the session reports and git.

## What was built
- **f135-01** (`runner/milestone.py`): `E2E_STOP` names the stop. `_reviewed` treats a recorded end-to-end stop as not reviewed when the project's `[checks]` names no end-to-end tests, so `due_reviews` picks it up again. With end-to-end tests named, the stop still waits for the owner. Two tests: the due/not-due cases (stale stop, a clean stop, a real end-to-end setup), and a review with no end-to-end tests that calls no command, logs the skip and reaches Claude's round.
- D1 had landed earlier, in commit 947dd8c (`run_e2e` returns `NO_E2E` when `[checks] e2e` is empty). The ticket keyed D2 on that same `[checks]` key instead of the `tests/e2e/` folder the card mentions. That is the better choice: it is the setting `run_e2e` actually reads.
- The rest of the milestone diff (`base.html`, `thread.html`, `deck.js`, the partials, the dashboard tests, the F19 and F28 reviews) belongs to F19's and F28's review rounds, which ran after this ticket. Those are reviewed in their own reports, not here.

## Findings and resolutions
None. The code is small, matches the card, and both Done-when lines were met in practice by the 07:10 and 07:34 reruns. The tests cover the stale stop, a non-end-to-end stop and the real-failure case, and they check that no command runs. There's no French in this milestone.

## Backlog
Nothing added.

## Factory
- **Flow:** one lead ticket, first attempt, no checkpoint findings, no stops other than the expected restart after a `runner/` change. The owner didn't need to step in.
- **Models:** Claude only (protected code), ≈272k token-equivalents for the ticket; the local model wasn't used, and that was right.
- **To change:** see "What next" and "What clogged".

<!-- runner report -->
<!-- /runner report -->
