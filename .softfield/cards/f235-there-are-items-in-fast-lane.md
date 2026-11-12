# Milestone F235: The fast lane goes before planner replies in the multi-project run

> **State:** done · **Priority:** 100 · **Area:** factory
> **Status: done.** Signed off by the owner on 2026-11-12. Base: git tag `f235-there-are-items-in-fast-lane-start`. Report: [`.softfield/reviews/f235-there-are-items-in-fast-lane.md`](../reviews/f235-there-are-items-in-fast-lane.md).
> Planted by the owner on 2026-11-09.

## Notes
There are items in fast lane, why did they not pick up as soon as Claude limit was available? Instead planner seemed to have gone first

### From F237: Why is the first ticket on the board, which is fast lane… (merged by the lead on 2026-11-09)
Why is the first ticket on the board, which is fast lane not being worked on right now

## What happened (2026-11-09)
Claude's 5-hour window reset at 16:00. Seven planner replies queued since 5–6 Nov ran 16:00–16:19 (about $28), then F139's fast-lane ticket f139-03 started at 16:19 and parked for the limit two minutes later, until 21:00. At 21:00 two planner replies (F234, then this one) went first again.

The cause is a runner bug, not a choice: ADR 35 item 2 says the lane goes before everything, and `dispatch.plan` (what Next in line shows) does put it first. But `softfield run` works through every project in rounds (`loop.project_round`, ADR 30 item 6), and a round runs each project's queued jobs before it offers any ticket, so the lane never reaches the pick until the planner's backlog is empty.

Again that evening (F237, merged here): from 21:00 three planner replies, then f86-01's direction, its last attempt on Qwen and Opus's escalation ran until 22:22, then two more planner replies. At 22:28 Next in line showed f139-03 first, but eight directions and a checkpoint were queued behind this reply, and the round runs all of those before it offers any ticket. Each direction leads to a last attempt on Qwen (f86-01's took 45 minutes) and sometimes an escalation, so the lane would wait for hours.

## Decisions
- **D1: a round starts with the fast lane.** `project_round` asks each project, in the owner's order, for its fast lane only (its lane tickets and the direction or escalation about one of them), then every project's queued jobs, then one ticket, as today. A pause skips the lane pass (ADR 35 item 5), so pausing is still how to get replies first. No ADR: this brings the runner in line with ADR 35, which is Accepted.

## Tickets
- f235-01-lane-before-every-projects-jobs (lead: `runner/` is protected)
