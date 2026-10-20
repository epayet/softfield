# Milestone F151: I had to restart the runner manually after f114-02, why.…

> **State:** ready · **Priority:** 10 · **Area:** factory
> Planted by the owner on 2026-10-17.

## Notes
I had to restart the runner manually after f114-02, why. It did a copilot checkpoint after that

## What happened (lead, 2026-10-19, from git, the run's notes and runner/loop.py)
- Session 2026-10-17 00:17. Claude was refused for the week (until Mon 19 Oct 17:00). At 02:54, after f68-02 and f69-01, the checkpoint came due: Copilot stood in, filed three fix tickets, and the checkpoint row parked until Monday for Claude's re-check (f8-08). Right as designed.
- Then f68-03, f69-02, f69-03, f114-01 and f114-02 merged (the last at 11:55): five unchecked merges, `checkpoint_every` is 2. No second stand-in ran: `note_merge` queues a checkpoint only when no checkpoint row exists, and the parked row still existed, due only at Monday's reset.
- Every ready developer ticket left waited for a lead ticket, and every lead ticket waited for Claude. So from 11:55 the runner held, idle, with nothing it could run. Left alone, it would have waited until Monday 17:00.
- The owner's restart at 13:00 unparks every parked row (`_unpark_row`, the `retry` flag), so the checkpoint ran at once: Claude still held, so Copilot stood in on the five merges (13:02) and filed f114-03 … f114-06, which kept the line busy until 21:29.
- The design meant this (f8-08, and `test_two_stand_in_checkpoints_then_claude_free_make_one_claude_recheck_of_all_their_merges`: "a stand-in reviews each batch of merges and one queued checkpoint gathers them"), but that test runs the parked row by hand; in the loop nothing ever starts it before its reset.

## Decisions
- D1. A merge that brings the unchecked merges to `checkpoint_every` while the checkpoint row is parked for a later reset starts that row again at the next pick (as a restart does), instead of leaving it parked. `checkpoint()` is unchanged: with Claude held, the stand-in reviews only the unchecked merges and the row parks again for Claude's re-check of them all; with Claude free, Claude's checkpoint runs early, which is better.
- D2. No ADR: it makes the loop do what f8-08 and ADR 16 item 9 already say. F140, Copilot takes checkpoints first, would remove the park after a stand-in altogether; this fix is one condition and holds until then.
