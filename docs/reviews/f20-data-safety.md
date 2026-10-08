# Review: F20 data safety

## Sign-off sheet

1. **What changed**
   - Once a day, the runner copies the metrics database (planning threads, your requests and desk items, the ratings) into `~/Dropbox/software-factory-backups`, keeping the last 14 copies. A copy that fails is a line in the session report, and the run carries on. The first copy is already there: `factory-metrics-20261008-0820.sqlite`.
   - Approving a card's plan now also commits its whole planning thread to `docs/planning/<card>.md`, in the same commit as the plan. Five are in already (F22, F28, F30, F32, F41).
   - New: how to restore a copy, in `docs/workflow.md` §Backups.
2. **How to test it yourself**
   1. Open your Dropbox (phone or web) and find `software-factory-backups`: there is a `factory-metrics-<date>-<time>.sqlite` from this morning, and a new one appears each day the runner runs.
   2. On GitHub or in the repo, open `docs/planning/f22-move-archive-button-on-planning-desk.md`: your messages and the lead's replies, oldest first, each with who and when.
   3. Approve the next plan from `/planning`, then look at the commit "F… plan approved by the owner": its thread file is in it.
3. **Left for later:** nothing from this review. The repeated points in the lead's replies (visible in the five exports) were F41's fix, which has since landed (fcb2d0c); the next approved plan's export will show whether it is gone.
4. **Decisions waiting for you:** none.
5. **How the work went**
   - [2026-10-08 07:47](../sessions/2026-10-08-0747.md): f20-01 (backup) merged first time, 34 min, lead only.
   - [2026-10-08 08:20](../sessions/2026-10-08-0820.md): f20-02 (thread export) merged first time, 31 min, lead only.
   - Lessons: reading the real output beats reading the tests. The exports showed every lead point twice, which the tests (built on clean messages) could not; it traced back to the planner prompt, already F41's work. And a backup isn't done until someone knows how to restore it: the milestone had no restore steps, the review added them.
6. **What next**
   - **Product:** on hold, as you asked (2026-10-04).
   - **Factory:** F40 ("Need back up code asap") is the other half of data safety: the code lives on one disk too, and the card is still an idea with no notes. I suggest the planner takes it next, with a daily push to a private remote as the simplest answer. F50 ("the data safety review it asks has no info") is now planned and ready: a card ripens only once its review exists, and the thread page shows the sign-off sheet.
7. **What clogged the factory line:** almost nothing for F20 itself: two lead tickets in two short runs (≈1 h), each ending with the restart a runner change needs. The restart between them is the only gap, and it's by design (m4-07).

## What was built

- **D1, backup** (`runner/backup.py`, `[backup]` in `workflow/runner.toml`): SQLite's online backup to a hidden `.part` file, switched out of WAL mode, then renamed into place, so Dropbox never sees a half copy or the live `-wal`/`-shm`. Due when the newest copy's name is older than `every_hours`; checked at the run's start, at each pick, during waits for Claude (hourly, or at each switch poll) and during your pause. While none is due a check costs one `stat` of the folder. A failure retries after 5 minutes and is noted once in the report until a copy works again. Pruning only touches files matching the name pattern.
- **D2, thread export** (`planner.export`, `requests._export`): every message oldest first under a `## The owner/The lead, <time>` heading, its body quoted so Markdown in a message can't break the file. A refused approval writes nothing; a failing commit removes a file it created.

## Findings and resolutions

| Id | Severity | Route | What | Resolution |
|---|---|---|---|---|
| f20-data-safety-F1 | should-fix | claude | No restore steps anywhere: the owner would have copies and no safe way back (a stale `-wal` next to a restored file is the trap). | Added `docs/workflow.md` §Backups. Resolved. |
| f20-data-safety-F2 | nit | claude | The export's undo path (the commit fails after the file is written) had no test. | Added `test_a_commit_that_fails_after_the_export_leaves_no_file`. Resolved. |

**Round 2:** both resolved. The restore steps match the code (`[metrics] db`, `[backup] dir`, `runner backfill`), and the new test passes. The commits since round 1 that touch `runner/requests.py` and `runner/planner.py` (f49-01, f31-05, F31 D1/F55, the merge settling) leave `_export` and its undo as they were; `runner/backup.py` is unchanged. `tests/runner/test_backup.py` and `test_planner.py`: 178 passed. No new finding.

Checked and fine: the tests cover each Done when, including the not-writable folder (run goes on, one note) and the long wait; no existing test was edited (only `test_planner.py`'s imports). No user-facing strings, so no French to check. Full suite green (1674 passed before the fixes; the new test passes).

No checkpoint ran (both tickets were the lead's), so there are no checkpoint findings to judge.

## Backlog

Nothing new.

## Workflow observations

- Both tickets were lead tickets on protected code and passed first time; for runner work of this size the lead-only path is cheap ($3.75 for the milestone).
- The doubled points in the exports are the clearest evidence yet for F41: the repo now keeps both copies forever. Once f41-01 lands, new exports will be half as long.
- F50 shows the desk can ask for a review before the review exists; see "What next".

<!-- runner report -->
## Numbers

_Written by `uv run runner report f20-data-safety` from the metrics database, which isn't in git: a snapshot. Run it again to refresh; edit outside these markers._

| Result | F20-DATA-SAFETY |
|---|---|
| Tickets merged | 2 of 2 |
| First-attempt pass rate | - |
| Local attempts | 0 |
| Escalations, directions, checkpoints | 0, 0, 0 |
| Review rounds | 1 |
| Findings | none |
| Local model | 0 tokens (0 in, 0 out) |
| Claude | $3.75 (757k token-equivalents) |

### Savings from delegating

What Claude would have spent writing the lines the developers merged, against what it spent supporting them: tickets, directions, escalations, and a share of the reviews and checkpoints (f1 D7). API-equivalent dollars.

| Developer | Tickets | Lines | Doing it itself | Supporting | Net |
|---|---|---|---|---|---|
| **All** | 0 | 0 | $0.00 | $0.00 | **$0.00** |

Tokens underneath: doing it itself ≈0 token-equivalents, supporting ≈0.

### By agent

| Agent | Jobs | Tokens (Claude: token-equivalents) | Dollars |
|---|---|---|---|
| claude-opus | 3 | 757k | $3.75 |

### Trends

| Milestone | Merged | First-attempt | Attempts | Claude | Net savings |
|---|---|---|---|---|---|
| m1 | 5 | 4/5 (80%) | 7 | $1.51 | -$0.63 |
| m2 | 4 | 4/5 (80%) | 6 | $3.45 | -$2.63 |
| m3 | 10 | 10/11 (91%) | 13 | $4.95 | -$1.12 |
| m4 | 11 | 7/11 (64%) | 28 | $1.02 | $12.29 |
| f1 | 48 | 15/22 (68%) | 45 | $83.85 | $33.24 |
| f6-planning-room | 30 | 7/15 (47%) | 32 | $55.75 | -$12.28 |
| bugs | 0 | - | 0 | $0.00 | $0.00 |
| f2 | 12 | 1/3 (33%) | 9 | $39.43 | -$3.00 |
| f3 | 25 | 2/16 (12%) | 50 | $54.52 | -$18.92 |
| f4-always-on | 31 | 10/21 (48%) | 42 | $26.27 | -$4.05 |
| f5-board | 8 | - | 0 | $16.16 | $0.00 |
| f7-factory-fixes | 7 | - | 0 | $12.96 | $0.00 |
| f8-one-queue | 11 | 2/3 (67%) | 5 | $24.14 | $1.20 |
| f9-line-polish | 9 | 4/9 (44%) | 21 | $2.18 | $4.00 |
| f10-crates | 0 | - | 0 | $0.00 | $0.00 |
| f11-test | 0 | - | 0 | $0.50 | $0.00 |
| f12-turn-on-notifications-little-feedback-button | 0 | - | 0 | $3.57 | $0.00 |
| f13-planting-idea-ui-feedback | 0 | - | 0 | $0.52 | $0.00 |
| f14-coming-planted-ideas-not-clickable | 0 | - | 0 | $0.87 | $0.00 |
| f15-reprioritising-tickets | 0 | - | 0 | $0.00 | $0.00 |
| f16-planning-still-says-your-answer-wanted | 0 | - | 0 | $0.42 | $0.00 |
| f17-tighter-running-and-pause-presence-in | 0 | - | 0 | $0.94 | $0.00 |
| f18-arrow-to-reprioririse-queue | 0 | - | 0 | $0.00 | $0.00 |
| f19-will-i-need-to-refresh-planning | 0 | - | 0 | $0.65 | $0.00 |
| f20-data-safety | 2 | - | 0 | $3.75 | $0.00 |
| f21-lead-briefs | 0 | - | 0 | $0.00 | $0.00 |
| f22-move-archive-button-on-planning-desk | 0 | - | 0 | $1.02 | $0.00 |
| f23-when-i-click-comment-on-the | 0 | - | 0 | $1.00 | $0.00 |
| f24-bug-when-i-answer-a-ticket | 0 | - | 0 | $0.45 | $0.00 |
| f25-whenever-i-plant-something-does-it | 0 | - | 0 | $1.90 | $0.00 |
| f26-i-want-to-see-numbers-next | 0 | - | 0 | $0.53 | $0.00 |
| f27-when-i-pause-the-factory-i | 0 | - | 0 | $3.31 | $0.00 |
| f28-the-first-time-i-clicked-on | 0 | - | 0 | $0.65 | $0.00 |
| f29 | 0 | - | 0 | $1.09 | $0.00 |
| f29-the-top-was-saying-resuming-but | 0 | - | 0 | $0.62 | $0.00 |
| f30-on-conversations-i-want-to-the | 0 | - | 0 | $0.59 | $0.00 |
| f31-when-i-click-on-approve-plan | 1 | - | 0 | $3.84 | $0.00 |
| f32-the-5-hour-lead-s-window | 0 | - | 0 | $0.59 | $0.00 |
| f33-overview-now-check-all-how-long | 0 | - | 0 | $0.73 | $0.00 |
| f34-planner-tasks-cannot-be-paused-but | 0 | - | 0 | $0.39 | $0.00 |
| f35-when-i-m-reviewing-what-s | 0 | - | 0 | $0.00 | $0.00 |
| f36-whenever-the-planner-is-planning-and | 0 | - | 0 | $0.00 | $0.00 |
| f37-in-planning-mode-it-tends-to | 0 | - | 0 | $0.00 | $0.00 |
| f38-the-refresh-prompt-causes-layout-shifting | 0 | - | 0 | $0.00 | $0.00 |
| f39-limits-on-tickets-per-milestone | 0 | - | 0 | $0.00 | $0.00 |
| f40-need-back-up-code-asap | 0 | - | 0 | $0.00 | $0.00 |
| f41-i-find-that-on-conversations-there | 0 | - | 0 | $0.72 | $0.00 |
| f42-the-space-for-me-to-scroll | 0 | - | 0 | $0.87 | $0.00 |
| f43-what-happens-when-a-proposal-has | 0 | - | 0 | $1.75 | $0.00 |
| f44 | 0 | - | 0 | $0.72 | $0.00 |
| f44-in-proposal-i-don-t-need | 0 | - | 0 | $0.39 | $0.00 |
| f45-when-i-approve-a-plan-it | 0 | - | 0 | $0.27 | $0.00 |
| f46-the-dismiss-cards-that-didn-t | 0 | - | 0 | $1.90 | $0.00 |
| f47-when-i-a-pprove-a-plan | 0 | - | 0 | $0.28 | $0.00 |
| f48-the-didnt-go-through-cards-try | 0 | - | 0 | $1.64 | $0.00 |
| f49-don-t-ask-me-to-merge | 0 | - | 0 | $0.87 | $0.00 |
| f50-the-data-safety-review-it-asks | 0 | - | 0 | $1.61 | $0.00 |
| m0 | 0 | - | 0 | $0.00 | $0.00 |
| **All** | 214 | 66/121 (55%) | 258 | $365.11 | $8.10 |
<!-- /runner report -->
