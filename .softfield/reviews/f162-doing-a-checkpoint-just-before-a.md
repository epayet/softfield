# Review: F162, no checkpoint on merges the milestone's review is about to read

- **Status:** round 1 done. One blocking bug and five smaller problems found, all fixed in this round.

**Expected outcome:** when a milestone's last ticket merges, its review starts at once: no checkpoint reads merges the review is about to read whole. Other milestones' merges still get theirs.

**Done when:** f162-01 is merged, and the next milestone that finishes on developer merges shows no checkpoint between its last merge and its review on the floor's log.

**Against that:** f162-01 is merged, and the tests show the behaviour. The floor's log can't show it yet, because F162's only ticket was a lead's. The next milestone finishing on developer merges is the real check.

## Sign-off sheet

### 1. What changed
- **A milestone's last merges go straight to its review.** The checkpoint that used to run just before it no longer does, so that's about a minute and $0.13–0.30 less on each such milestone (the figures in ADR 38).
- **The floor's log says so,** in one line: "no checkpoint: F23's review reads f23-04, f23-05".
- **Other milestones keep their checkpoints.** If a merge from a milestone still being built is waiting, it stays in the count.
- **A review's last-round fixes keep their checkpoint.** No later round reads them, so the checkpoint is still their only reader.

No page changes, and nothing changes in Coucou.

### 2. How to test it yourself
1. Wait for the next milestone that ends on developer merges. There's nothing to set up.
2. Open the floor's log when its last ticket merges.
3. You should see "no checkpoint: …'s review reads …", then its review starting, with no checkpoint between them.

### 3. Left for later
No bug tickets set aside. Two small points are only reported below, under Findings (F7 and F8).

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-04, 12:48: the first attempt at f162-01 failed after 21 minutes (Sonnet, job 1777), and the lead's look at it failed after 16 minutes (job 1778), both under the expired login.
- 2026-11-04, 21:02: the second attempt merged f162-01 in 15 minutes for $0.81 (Sonnet, job 1783). Session report: [`2026-11-04-2054`](../sessions/2026-11-04-2054.md). The local model processed no tokens, because `runner/` is protected.
- 2026-11-04, 21:21: review round 1 found six problems and fixed them.
- Lessons:
  - **The plan misread `restart`.** ADR 38 says a review with fix tickets stops at `restart`, but that only happens when the runner's own code changed. Fixes normally merge inside the review's loop, so the rule needed a case for the last round. It has one now, with a test.
  - **A test can pass without reaching its case.** The main test's comment said "still building" when its milestone was already complete. It now asserts that state before going on.
  - **Stopping early leaves state behind.** A checkpoint finishing with no job left a parked session for the next one to resume. That's fixed too.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** when a plan rests on a runner state such as `restart`, the planner should read the code that sets it, not just the words around it. I've noted this in ADR 02's log, and I wouldn't add a gate for it.
- **Factory:** the runner and dashboard test suite takes over 10 minutes, longer than a single command is allowed here. A quicker test run, or a longer limit for reviews, would stop that getting in the way. I suggest looking at the slowest tests first.

### 7. What clogged the factory line
- **The expired login: 37 minutes of failed jobs on this milestone (12:48 to 13:25).** bug-59 is merged and now holds Claude's jobs instead.
- **Waiting for a login: about 7 hours (13:25 to 20:33).** F203's review counted the same hours. Nothing ran, and bug-59's desk item now asks you to log in.
- **Other jobs running first: about 30 minutes (20:33 to 21:02).** F203's review, bug-59 and F219's plan ran before this ticket's second attempt. The runner does one job at a time, and only parallel workers would change that. They're last on your priority list, so I'd do nothing here.

The build itself took 15 minutes.

## What was built
`_drop_covered_merges` in `runner/loop.py` takes out of `unchecked` and `recheck` any merge whose milestone's review is due or stopped at `restart`, and logs one line. `note_merge` calls it before its count, and `checkpoint` calls it at its start, so a checkpoint left with nothing finishes without a job.

**Existing tests the ticket edited:** five tests and two helpers (`_two_merges`, `_four_merges`) gained a ticket that never runs, to keep their milestone building and their checkpoint due, and one test's fix ticket moved from `m1-03` to `m1-04` as a result. These edits are sound: they keep the tests about what they were testing.

No French changed: the factory's log is in English.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | blocking | claude | Fixes merged after a review's last round were dropped from the checkpoint, and no round read them | Fixed: `Session.last_round` marks that round's queue, and those merges keep their checkpoint. Reproduced without the fix: the log said "M1's review reads m1-05-fix" with no round left. |
| F2 | should-fix | claude | A parked checkpoint left with no merges kept its session, so the next one would resume it instead of reading its own merges | Fixed: the session goes when the lists empty. New test. |
| F3 | should-fix | claude | A lead ticket completing a milestone left its developer merge unchecked, and a later checkpoint read it after the review had | Fixed: the drop runs on any done merge. New test. |
| F4 | should-fix | claude | The last-merge test never reached its case, and the stand-in's batch had no test | Fixed: the test keeps the milestone building and asserts it. New test for `recheck`. |
| F5 | should-fix | claude | A review at `restart` with no round left returned `restart` again, so the runner would restart for ever | Fixed: it stops as "review rounds used up". New test. Older code, seen by reading and in the test, not in a real run. |
| F6 | should-fix | claude | `docs/workflow.md` still said every two developer merges get a checkpoint | Fixed: both lines name ADR 38. |
| F7 | nit | report | Three or more fix tickets between rounds still queue a checkpoint on the first two | Not fixed: it follows the ADR's decision, and later fixes build on them. If it shows up as waste, mark a round that has a successor the same way as `last_round`. |
| F8 | nit | report | After a restart on a review's last round, developer fix merges still count as covered | Not fixed: it needs a lead fix and a developer fix on the same last round. If it happens, count `restart` as covered only while rounds remain. |

What held up when I looked for trouble:
- **A milestone stopped for good, or signed off:** it isn't due, so its later fix merges get a checkpoint as before.
- **A ticket with no file in `done/`, or one that doesn't parse:** it stays in the list, so nothing is dropped by mistake.
- **`bugs` tickets:** never covered, as `due_reviews` leaves them out.
- **A long key against a short one:** every comparison goes through `short_key`.
- **A queued checkpoint under a Claude limit:** the drop runs before the limit check, so an empty one needs no Claude and no stand-in.

Checkpoints: none read this ticket, so there's nothing to judge and no "missed".

## What was set aside
F7 and F8, as above. No bug tickets: neither is worth a run yet.

## Workflow observations
- **Checks run in this review:** `ruff` and `mypy` pass. No single test run finished the whole of `tests/runner tests/factory_dashboard`, because the time limit stopped it. In pieces, with no failure in any: the combined run passed all of `tests/runner` before it was stopped, then `test_loop.py` (355) and `test_milestone.py` (51) passed again on their own. A dashboard run reached about 95% with no failure before the limit stopped it (a few `E` marks print only after the kill, as tests lost their processes), and the last files (`test_reports`, `test_requests`, `test_runs`, `test_thread`, `test_tickets`, `test_timeline`) passed separately, as did `test_board` and `test_overview`. `softfield check-all` was not run. That the combined run got through `tests/runner` is worked out from its progress (it stopped at about 82%, and the runner's tests are about 62% of the total), since it printed no summary.
- **Score: 6 of 10.** The ticket did what it asked and its tests were mostly good, but the design carried a real hole. The cause was in the plan more than the build.
- **ADR 38's wording on `restart` is inexact:** its Context and item 1 describe fix tickets waiting under `restart`. I left the accepted ADR as it is. This report and ADR 02's log hold the correction, and the code handles both cases.
- **`softfield report` isn't among the commands a review may run,** so the numbers below come from the runner.
- The ADR 02 entry is added. `lead.md` asks to update a "Known range" that it no longer has, so there was nothing to update there.

<!-- runner report -->
<!-- /runner report -->
