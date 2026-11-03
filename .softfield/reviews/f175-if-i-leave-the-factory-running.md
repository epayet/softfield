# Review: F175, the factory cleans up its temp files, so the disk stops filling

## Sign-off sheet

### 1. What changed
- **Every job now has its own temp folder, deleted when the job ends,** however it ends: finished, timed out or stopped. Until now, a killed job's temp files stayed in `/tmp` until the next reboot.
- **Leftovers are swept when the runner starts.** If a runner died without cleaning up, the next start removes what it left, and nothing else in `/tmp`.
- **Test runs are much lighter.** Each temporary test repo carried about fifteen sample files from git. That came to over a million files, nearly all of `/tmp`'s weight. They no longer carry them.
- **What should improve:** free space should stop shrinking while the factory runs, and the next boot should be quick.
- **The lead can now measure where the space goes,** read-only, in one command.
- **Not proven yet: the 30 GB.** On 2026-10-30, `/tmp` measured about 7 GB, of which test runs were 6.5 GB. That is the largest cause found, but it is not 30 GB. Those sizes also read low, because the measure counted files' length rather than the space they take (fixed in this review). Only the check below on your computer can settle it.

### 2. How to test it yourself
1. Note the free space on your computer, for example in Ubuntu's Disk Usage Analyzer.
2. Leave the factory working for a few days, as you did when you lost the 30 GB. Don't reboot during that time.
3. Note the free space again, then reboot. The boot should not be slow.
4. Note the free space after the reboot. A few hundred MB coming back is fine. Tens of GB coming back means something is still filling the disk: tell me and I'll measure it before you reboot next time.

### 3. Left for later
- The job logs still grow slowly (see Decisions below).
- **bug-06** is set aside and worth queueing: it lets a review see the whole test suite finish (see What next).

### 4. Decisions waiting for you
- **[ADR 39: bound the run logs](../adr/39-bound-the-run-logs.md).** The job logs take about 800 MB, growing by a few MB a day, and nothing limits them. It isn't urgent. I recommend compressing logs older than 90 days, so you keep every one, and not deleting any. The logs aren't in your daily Dropbox backup, so deleting them would lose them for good unless the backup takes them first.

### 5. How the work went
- 2026-10-30 04:24 ([session](../sessions/2026-10-30-0424.md)): f175-01, the disk measure, passed first time on Sonnet ($0.58).
- 2026-10-30 05:08 ([session](../sessions/2026-10-30-0508.md)): f175-02, one temp folder per job, passed first time on Opus ($1.02).
- 2026-10-30 05:22 ([session](../sessions/2026-10-30-0522.md)): f175-03, measure again and fix, passed first time on Sonnet ($0.34).
- 2026-10-30 05:32 and 2026-11-03: this review. Its first run was interrupted and it resumed four days later.
- 2026-11-03 08:54 ([session](../sessions/2026-11-03-0854.md)): review round 1 finished ($3.63 for that job), five fixes made. Round 2 followed at 09:15: the fixes hold.
- **Lessons:**
  - Measuring first paid off. The plan expected killed jobs to be the cause, but the measure pointed at sample files in test repos, a small fix the plan hadn't foreseen.
  - A clean-up step must never be able to stop the work. The new temp folder made commands fail on a full disk, the very case this card is about. Fixed, with tests.
  - A measuring tool needs checking against what it claims to measure. `look disk` read files' length, not the disk space they take, and its tests couldn't tell the difference. Fixed, with a test that can.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:**
  - Decide ADR 39 when you have a moment. Nothing depends on it.
  - Queue bug-06. This review's first attempt at the whole test suite ran out of its 10-minute limit at about 65%. With the 16 workers bug-06 proposes, the same suite took under 4 minutes.
  - Run f123-02 when its turn comes: it also replaces a test that failed once here for no reason I could find.

### 7. What clogged the factory line
From the jobs and runs tables. The three tickets themselves took 30 minutes of work.
- **The review's wait, about 4 days.** The tickets were merged by 05:28 on 2026-10-30, and the review only finished on 2026-11-03. Its job shows 28.65 hours open and then "interrupted", but a review is limited to 30 minutes, so most of that can't be work. No run started between 2026-10-31 10:11 and 2026-11-02 22:10, and on 2026-11-02 at 22:32 Claude's 5-hour limit refused a job. The database doesn't say why the first run stopped. **To unclog:** the runner closing a dead job's row as soon as it can tell, so the hours read true; a ticket only if you see it again.
- **A test run that couldn't finish, 10 minutes.** The suite is longer than one call allows without workers. **To unclog:** bug-06.
- **Waiting behind another card, 30 minutes.** F185's review ran between f175-01 and f175-02. Nothing to change.
- **A failed start, 5 seconds.** f175-01 failed once on 2026-10-29, within seconds. Nothing to change.
- No stops for you and no failed attempts on the work itself.

## What was built
- `runner/procs.py`: `_start` gives each command a folder `/tmp/softfield-<uid>/<runner pid>-<random>` as `TMPDIR`; `_owned` and `stop_all` remove it once the group is killed. A nested command keeps its job's folder (D2). `sweep_tmp` removes the folders of dead runners (D3), called at `softfield run` in `runner/cli.py`.
- `runner/look.py`: `softfield look disk` (D4).
- `tests/conftest.py`: an empty `GIT_TEMPLATE_DIR` for the whole test session.
- [ADR 39](../adr/39-bound-the-run-logs.md), drafted by f175-03 and corrected here.

## Findings and resolutions
No blocking findings. All fixed by the review, as the code is protected and each fix is small:

| Id | Grade | Finding | Resolution |
|---|---|---|---|
| F1 | should-fix | `look disk` reported files' length and left out folders: 300 one-byte files read 0.0 MB and take 1.3 MB | Reads the blocks used; test seen failing first; card's earlier figures marked |
| F2 | should-fix | A full disk made commands raise through the new temp folder, and could stop `softfield run` in its sweep | Runs without a folder; two tests, both seen failing first |
| F3 | nit | A deleted file held by several processes counted once per process | Counted once; test seen failing first |
| F4 | nit | A held-open assertion passed on almost anything; a failed start had no test | Exact line; new test, which passed at once because the code was already right |
| F5 | nit | ADR 39 made deletion wait on a backup that doesn't hold the logs | Corrected, recommendation added |
| F8 | nit | Round 1's "up 13 MB in four days" for the logs subtracted a length from a later reading, and the logs took 799.5 MB by round 2 | Found in round 2; this sheet and ADR 39 now say about 800 MB and a few MB a day |

**Round 2:** F1 to F5 re-read in the fix diffs and all hold. The new tests separate what they claim to: the disk test fails on files' length, the held-open test fails on a count per process, and the full-disk tests fail if the error escapes. Nothing new in the code.

Said here only (route `report`):
- **F6:** `test_send_lights_up_only_for_another_order_and_sends_the_names` timed out once in three full parallel runs, and passed in the other two and in two smaller runs. This card doesn't touch that page, and I did not find the cause. f123-02 replaces the test.
- **F7:** from reading the code, not seen happening: a folder can stay when its runner's pid was reused or the runner lives on, and a folder a job made unreadable can't be removed. Each would be small, and a reboot empties them.

**What was checked:**
- **Tests:** in round 2, a full run on 16 workers passed, 2,926 of 2,926, in 3 min 16 s; so did the last one in round 1, and the one before it had the F6 failure. A run without workers can't finish inside one call, so it wasn't completed.
- **Gates:** `softfield check-all` passed after round 1's last code edit (ruff, format, mypy, translations, layout, tests). Round 2 changed only words in the review, ADR 39 and ADR 02, so it ran the tests and not `check-all` again.
- **Edited tests:** the only existing test the developers' work changed is in `test_cli.py`, by an added import. Every other test is new.
- **Live reading, 2026-11-03:** `/tmp` is 46–76 MB, of which this job's own folder is most. This is no proof of the fix on its own: the 63 old `tmp*.sqlite` files are gone too, so there has been a reboot since the last measure.
- **French:** none, as the factory has no translations and no words changed.
- **Checkpoints:** none ran on this card (lead tickets), so there is nothing to judge.

Score 7: the design is sound and simple, and all three tickets passed first time. Two should-fix points remained, though, one of them on the case the card exists for.

## Set aside
Nothing new. bug-06 was already set aside.

## Factory
- **Flow:** three lead tickets, all first time. No stops for the owner, no escalation, no checkpoint. Two rounds of review: the first resumed after an interruption and changed the runner, so the runner restarted (15 seconds) before the second.
- **Models:** Sonnet 2/2 ($0.92), Opus 1/1 ($1.02), planning $1.76 on Opus. No local model work.
- **The move under the review:** the first run stopped before F139 moved `.factory/` to `.softfield/`, so the resumed brief named a path that no longer exists (its output file, the backlog). ADR 35 had also retired the backlog. The resumed job had to work this out by reading the code.
- **What to change:** a resumed job should be given its output path again, as the runner now computes it. It's small, and it only matters when a job resumes across such a move, so it stays here rather than becoming a ticket. Queue bug-06.

<!-- runner report -->
<!-- /runner report -->
