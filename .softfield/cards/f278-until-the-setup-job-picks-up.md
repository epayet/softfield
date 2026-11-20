# Milestone F278: A new project's M1 waits on the desk while its setup runs, not as a seed

> **State:** ready · **Area:** factory
> Planted by the owner on 2026-11-19.

## Notes
until the setup job picks up the work to make the first adr, the planning says to wait for m1. that's ok, but there's a seed of the first thing, which disappears after the setup starts. it's a bit confusing

## What happens today
From the code and duck-ascii-test's rows (2026-11-19):
- 16:04 the runner makes the project (`setup.start_project`): M1 goes on the board as an idea, and its `setup` job is queued on M1's thread (`requests._new_project`). No thread exists yet, so the desk's `_seeds` (`factory_dashboard/planning.py`) lists M1 under "Seeds, not asked about yet", while the setup strip says "The lead's setup is next in line. Its answer comes on M1."
- 16:10 the setup job starts and makes M1's thread with no message in it. M1 is no longer a seed, and it isn't in "Your answers wanted" either: `_waiting_order` only counts a thread whose last message is the owner's or the runner's. For two minutes M1 is on no part of the desk.
- 16:12 the lead's first message: M1 comes back under "Your answers wanted".

## Decisions
- **D1. An open setup job puts its card on the desk as a reply on its way.** While a `setup` job is open (queued or running) on a thread, that card is one of the threads the lead owes a reply (`_waiting_order`), whatever its thread holds, even when there is no thread yet. So from the moment the project exists, M1 shows under "Your answers wanted", dashed and on its way, with the same words as any reply waiting ("waiting for the lead · …", then "the lead is writing this reply · …" once it runs). The Seeds group never lists a card that `_waiting_order` lists. No new look: it is the existing dashed row.
