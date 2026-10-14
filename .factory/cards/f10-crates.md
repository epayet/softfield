# Milestone F10: crates on the belts

> **Status: planned** (2026-10-06, with the owner). **State:** ready · **Priority:** 5 · **Area:** factory
> **After:** f6-planning-room signed off (the owner, 2026-10-06: crates after the planning room; without it, its lead ticket would go before F6's developer tickets)
> From the roadmap's "Crates move along the belts" (after F8, which made every job a queue row) and the owner's notes of 2026-10-06: "I want to see one crate moving on the conveyor belt at a time when it's doing work", "there was a time when the developer was working but the belt wasn't moving", and "Running: check-all · f6-06, but the line wasn't moving".

## Outcome
- Whatever runs (a ticket's attempt, the runner's own gates, a lead's finish, a checkpoint, an escalation, a review, a planner reply) is one crate on the floor, travelling the belt to the machine doing it, then on to checks and merged. One at a time, since the runner does one job at a time.
- A machine that works always has its crate, and the belt that brought it moves.
- Replay shows the same motion.

## Why the belt stood still
- `live_line` (`factory_dashboard/line.py`) marks a belt `carrying` from the crate's last logged trip. A job with no trip yet, or work that isn't a job (the runner's `check-all` on a lead's finish, the gates between attempts), moves nothing.

## Tickets
| # | Ticket | Who | d | Depends on | What |
|---|---|---|---|---|---|
| 01 | crate-per-job | L | 7 | – | the motion's core: one crate per running job of any kind, including the runner's gates; the belt it rides moves; live and replay |
| 02 | replan | L | 3 | 01 | check this doc against 01, and write the small developer tickets (one per job kind's look, the replay's motion) |

Developer tickets come from 02, on top of 01's core (F3's lesson: no SVG geometry for developers).
