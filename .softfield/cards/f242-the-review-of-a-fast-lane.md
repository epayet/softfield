# Milestone F242: A fast-lane card's review goes in the fast lane

> **State:** ready · **Priority:** 1 · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-11-11.

## Notes
The review of a fast lane ticket doesn't seem to get prioritised as fast lane, runner went onto other things rather than the milestone review. Reviews are important as the lead can catch bugs

## What happened (lead, 2026-11-11)
- **F191, Why is the lead reviewing something, in the fast lane since 02:09:** its last ticket merged, and its review was queued at **08:33** (`work_queue` row 697). Claude was in the owner's share of the 5-hour window, so `park_review` parked it until **10:30**. A fast-lane ticket would have run: the lane may use both reserves (ADR 35 item 4), a review only the week's (`claude_hold` without `owners`).
- Meanwhile the line took developer tickets: `f210-03-typed-comments-wait` (08:33–09:03), then `f77-02-one-allowance-bar` (09:03–10:47), which was still running at 10:30. The review ran **10:47–11:28**: 2 h 15 late.
- **Cause 1, the lane stops at the last ticket:** the lane (`first` for `dispatch.pick`) is made of ready ticket ids (`reserve_cards`, `lane_with_escalated`). Once a card's tickets are all done, it has none, so its review is an ordinary queued job: behind every planner job, escalation, direction and checkpoint, and left out of the round's lane pass (`project_round`, `lane_only`).
- **Cause 2, the reserves:** `park_review` asks `claude_hold` as for any support job, so a lane card's review parks where its tickets would have run.
- **Cause 3, the review's turn:** `_queue_due_review` queues the first due review in milestone order, one at a time, and none while any checkpoint or escalation is queued, whatever its card: a lane card's review can wait behind another card's review or checkpoint.

## Decisions
- **D1: a lane card's review is in the lane.** The lane's `first` also takes the full keys of the cards marked fast lane (`**Fast lane:** yes`, the mark `reserve_cards` reads; not on its way out, as F192 D4), whether or not they have a ready ticket, in `work_queue` and `dry_run_plan` alike. `dispatch.plan` treats a queued `review` whose subject is in `first` as a lane row: a new `dispatch.LANE_KINDS = (ESCALATION, DIRECTION, REVIEW)` replaces `GOES_WITH` in the lane test; `GOES_WITH` keeps its meaning (a ticket's own work). The lane's queued rows go by kind and age, then the lane's tickets. The round's lane pass (`lane_only`) takes it too.
- **D2: its turn to be queued.** `_queue_due_review` puts the due reviews of lane cards first. A lane card's review waits only for a checkpoint or an escalation of its own card (an escalation's subject starts with its short key, a checkpoint's is its full key), and `_runnable_rows` lets it through on the same terms. Other reviews keep today's rule.
- **D3: its reserves are the lane's.** `park_review` of a lane card parks only where a lane ticket would: both reserves may be used (ADR 35 item 4), never a real limit or an expired login. The same in a round (F191 D4).
- **D4: Next in line shows it in the Fast lane bay,** as F191 D3 did for an escalation whose ticket left `ready/`: a queued review whose subject's short key is a lane card's. Nothing new is drawn.
- **Unchanged:** a running ticket is never stopped for a review (the 17 minutes of `f77-02` past 10:30 stay); a review's fixes follow F191 D7, and a lane card's fixes are lane tickets already; the owner's pause holds the lane's review as it holds the lane (ADR 35 item 5).

## Plan
- `f242-01-lane-review-goes-first` (lead, runner: D1–D3).
- `f242-02-lane-review-in-the-bay` (developer, dashboard: D4), waits for 01.
- No mock-up: the review row already exists on Next in line, and only moves to the Fast lane bay, drawn in `.softfield/cards/f172-mockup/goes-first.html`.
