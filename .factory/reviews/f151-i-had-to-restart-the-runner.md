# Review: F151, I had to restart the runner

## Sign-off sheet

### 1. What changed
While Claude is held, the runner no longer sits idle after a checkpoint's first stand-in. Before, once Copilot had stood in for a checkpoint, the checkpoint waited for Claude's reset (up to days), and every later batch of merges went unreviewed until you restarted the runner (17 Oct, after f114-02). Now each new batch of `checkpoint_every` developer merges starts the waiting checkpoint again at the next pick: Copilot reviews that batch, files its fix tickets, and the checkpoint goes back to waiting for Claude's re-check of everything. You don't need to restart the runner for it.

### 2. How to test it yourself
1. Next time Claude is held for the week (or its 5-hour share) and developer tickets are running, open the dashboard's queue.
2. After two developer merges, a checkpoint appears and Copilot's stand-in runs; the checkpoint then shows as waiting until Claude's reset.
3. After two more merges, without touching the runner, the same checkpoint runs again within a pick or two: a second Copilot stand-in names only the two new merges, and its fix tickets (if any) appear in the queue.
4. When Claude is back, one Claude checkpoint re-checks all four merges.

### 3. Left for later
- One nit in `docs/backlog.md` (F2): when the stand-in can't run (past its cap, or its job fails), the waiting checkpoint is tried again on every later merge, not only every second one: a repeated note in the session report, or another paid Copilot request. Bounded by the cap; F140 (Copilot takes checkpoints first) would remove the cause.

### 4. Decisions waiting for you
None. The card's D2 holds: this makes the loop do what f8-08 and ADR 16 item 9 already said, so no ADR.

### 5. How the work went
- 2026-10-22 20:47 ([session](../sessions/2026-10-22-2047.md)): 1 ticket, `f151-01-stand-in-on-each-batch`, built by the lead (runner code is Claude's), merged first time in 13.5 minutes for $0.84; 0 local tokens. The runner then stopped, as designed, because `runner/` changed.
- Lessons: the bug hid behind a test that started the parked row by hand (the card's "What happened"), so a loop-level test is what pinned it. The ticket's own "no stand-in" test didn't reach the new branch; the review added the missing case.

### 6. What next
- **Product:** on hold, as you asked (factory first).
- **Factory:** F140 (Copilot takes checkpoints first) makes this whole park-and-restart dance unnecessary and is the natural next step; when it lands, drop the unpark branch in `note_merge` and the F2 backlog nit with it. More widely: a test that drives a scheduling rule by hand (instead of through `work_queue`) is worth a second look in reviews, since that's how this one slipped.

### 7. What clogged the factory line
- The original incident (17 Oct): from 11:55 to the owner's restart at 13:00 the runner held idle, every ready ticket waiting on a checkpoint parked until Monday 17:00. This milestone is the unclog.
- This milestone's own run: 19.9 minutes, one 13.5-minute lead job; nothing waited on limits, failed attempts or the owner. The run ended on the designed stop for a `runner/` change; a fresh process is the only cost.

## What was built
`note_merge` (`runner/loop.py`): when a developer merge brings the unchecked merges to `checkpoint_every` while the checkpoint row already exists, parked until a later time, and holds merges a stand-in reviewed (`state.recheck`), the row is unparked (`_unpark_row`, as a restart does). `checkpoint()` is unchanged: with Claude still held, the stand-in reviews only the unchecked merges and the row parks again; with Claude free, Claude's checkpoint runs early. A row parked only for Claude's limit, with nothing a stand-in reviewed, still waits for its reset.

Tests (`tests/runner/test_loop.py`): two new loop-level tests from the ticket (each batch gets its stand-in; without a stand-in the row stays parked), and one from this review. No existing test was edited.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | claude | No test for a restarted checkpoint whose stand-in can't run: the ticket's "no stand-in" test has empty `recheck`, so it never takes the new branch | Fixed: `test_a_stand_in_that_fails_on_the_next_batch_parks_the_checkpoint_again_for_claude` (first stand-in passes, second fails, row parks again with both batches kept) |
| F2 | nit | backlog | Unpark fires on every merge at or past `checkpoint_every`, so a capped or failing stand-in is retried each merge | `docs/backlog.md`, likely superseded by F140 |

No checkpoint ran in this milestone (its only ticket was a lead ticket), so there are no checkpoint verdicts. Score: 8/10: a small, correct change that matches D1 exactly, with a good loop-level regression test; one acceptance case was untested.

The French: no `coucou/locale/fr/` change in this milestone.

## Factory
- Flow: one lead ticket, first attempt, no stops for the owner, no limit waits, no parks; the designed stop for a `runner/` change ended the run.
- Models: Claude Opus built it ($0.84, 25 steps); the local model had nothing to do (protected code).
- What to change: when a ticket's acceptance lists a "falls back as today" case, its test should take the new code path and then fall back, not skip the path entirely. Worth a line in `docs/task-writing.md` if it recurs; once is not a pattern yet.

<!-- runner report -->
<!-- /runner report -->
