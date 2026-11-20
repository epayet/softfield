# Milestone F277: A project's setup goes before every other job the runner could pick

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
why did the runner decide to pick a planner task rather than a setup task. setup is more important

## What happened (2026-11-19)
From the metrics database (`work_queue`, `jobs`, `runs`):
- 16:04:54: one batch of the owner's requests, applied in Softfield's turn, started duck-ascii-test (its `setup` row 884) and queued the reply on F275 (row 885).
- 16:05:16 to 16:07:51: Softfield's planner answered F275. duck-ascii-test had no session yet: `run_projects` reads the projects only at the start of a round, so the turn that applied the request ran its own queued job.
- 16:07:52: duck-ascii-test's session opened (run 1014), first in the projects' order (priority 1, Softfield 5).
- 16:08:15 to 16:10:29: Softfield's planner answered F276 anyway, queued at 16:07:59 in the same round. Why the duck's second pass picked nothing is not yet known: its run log is the place to look.
- 16:10:37 to 16:12:41: the setup ran, about 2 minutes.

waifu-gallery's setup waited the same way at 09:47 (behind F122's reply).

## Decisions
- **D1. A setup goes first.** In a round of `softfield run`, a project being set up (paused "setting up") with an open `setup` row runs it before anything else in the round: before the fast lane, every project's planner replies, directions, checkpoints and tickets. The owner's pause doesn't hold it, as today. A setup is short (about 2 minutes on Opus) and the owner is watching the Projects page for it.
- **D2. A project started mid-turn ends the turn.** When applying the owner's requests starts a project, that turn runs nothing more: the round ends, the next one reads the projects again and the setup goes first (D1).
- **D3. The second skip is found and fixed.** The ticket finds why duck-ascii-test's first round (16:07:52) didn't run its setup in the queued-jobs pass, and fixes it, with a test that fails without the fix.
