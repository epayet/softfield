# Milestone F191: The fast lane goes first under softfield run too, escalations included

> **State:** ready · **Priority:** 0 · **Area:** factory · **Fast lane:** yes
> Planted by the owner on 2026-10-29.

## Notes
Why is the lead reviewing something not on the fast lane? It reviewed f21 but there were fast lane work to do?

### From F238: During a milestone review, the runner applies other jobs… (merged by the lead on 2026-11-10)
During a milestone review, the runner applies other jobs requests so that planning response, and approvals don't wait. Currently, a non fast lane milestone review triggered a fix instead of picking up my planning approvals and questions

What was said on F238's thread:
The owner: during a milestone review, the runner should still apply other requests, so planning replies and approvals don't wait. Instead, F9's review (not in the fast lane) ran its fix tickets first. What the lead found (2026-11-10): round 1 ran from 14:24 to 14:51. Then the review's own queue ran f9-35 (14:51 to 15:20) and f9-36 (15:20 to 17:43, two attempts, a direction and a last attempt on the local model). Softfield's requests from 15:28 to 16:42 (a plant, the approvals of F211 and F236, a reorder, two removals) were applied only at 17:30. coaster-ranker's requests (accept ADR 1 and approve M1's plan at 14:31, a plant at 16:37) were still waiting at 17:45, because a review runs inline and every other project waits for it. Still open: the lead proposes to rewrite f191-05 so that, under softfield run, a round's fix tickets run in the main queue, behind every project's queued jobs and requests and ahead of other tickets, with no checkpoint before the next round. A request sent during a long ticket still waits for that ticket to end, as before.

### From F240: Why is it replying to planning thread lower on project… (merged by the lead on 2026-11-10)
Why is it replying to planning thread lower on project list? There are seeds and approvals pending on coaster ranker but the lead is currently replying to softfield thread

## What happened (lead, 2026-10-29)
- **21:06 to 22:17:** F21's review ran two rounds ($3.16, 70 minutes) while F85's `f85-01-pictures-at-the-review` and F175's `f175-01-look-disk` and `f175-02-one-temp-folder-per-job`, all in the fast lane and free to run, waited.
- **Cause 1, every project's queued jobs go first:** `softfield run` runs every project (ADR 30 item 6). Each round, `project_round` (`runner/loop.py`) first runs every project's queued jobs with `take_tickets=False`, and only then a ticket. In that first pass `_next_task` is never asked, so no lane ticket is there to beat the queued review (or a planner job, a checkpoint, a direction). F172's tests checked the order inside one `work_queue` call, never the round. Seen again on 2026-11-09: at the week's reset (16:00) seven planner jobs ran before `f139-03-rebuild-clashing-plan-branches`, in the fast lane, took the 5-hour window from 14% to 92%, and the lane ticket was refused two minutes in; after the 21:00 reset, ten more queued jobs (planner jobs, a direction, an escalation) went before it again.
- **Cause 2, an escalated ticket leaves the lane:** an escalation moves its ticket from `ready/` to `escalated/`, and `reserve_cards` reads `ready/` only, so the escalation of a lane ticket loses its place. 20:12 to 20:30, four planner jobs ran before the escalations of `f172-06-next-in-line-marked-first` and `f146-02-developers-only-view`. Next in line (`factory_dashboard/overview.py`) has the same gap.

## The owner, 2026-10-30
"Also, Factory is currently stuck because a review for a fast lane ticket is waiting for Claude tokens to come back. It should continue other developer tickets in the meantime."

## What happened (lead, 2026-11-02)
- **30 Oct 05:32:** F175's review started with the week at 99%, which a review may use (ADR 15 item 4). **05:54:** Claude refused it, the week at 100% until 2 Nov 16:00. The review slept in place. No job ran in any project until it was interrupted on 31 Oct at 10:11, 28 hours later.
- **Cause 3, a limit inside a round sleeps:** F53 D1 checks Claude before a round (`park_review`). Inside the round, `review_milestone` calls `call_claude` without `park`, so a refusal is waited out, and `run_projects` runs a review inline: every project stops with it. It has nothing to do with the fast lane: any review does this.
- **Cause 4, a review's inner queue sleeps too:** after a round, `review_milestone` runs `work_queue(s, milestone=milestone)`, whose `wait` defaults to True. With nothing it can run, `_wait_for_reset` sleeps to the first reset of a parked fix ticket or of any parked queued job, a planner's or a checkpoint's too, with the same result. A lead fix the week's pace line passes over no longer sleeps (F219 D3); the rest still do.
- **Cause 5, a ticket's repair turn:** `_repair_ticket` calls `call_claude` without `park`, after a checkpoint or an escalation wrote a ticket that fails pre-flight.
- **An expired login does the same (bug-59, on main since 2026-11-04):** `call_claude` without `park` waits in place for a new login, five minutes at a time, so a review round and a repair turn stop every project until the owner logs in.

## What happened (lead, 2026-11-10)
- **Cause 6, a review runs its fixes itself (from F238):** F9's review ran round 1 from 14:24 to 14:51, then its own queue, `work_queue(s, milestone=milestone)` in `review_milestone`, ran f9-35 and f9-36 until 17:43. That queue takes only F9's tickets and jobs, and the review runs inside `run_projects`' turn, so Softfield's requests from 15:28 waited until 17:30 and coaster-ranker's from 14:31 were still waiting at 17:45. Nothing was limited: this is D5's queue doing its normal work. It also runs every queued job of its own project, planner jobs included, so at 17:45 the lead was answering Softfield's threads (F238, F191, F240) from inside F9's review while coaster-ranker, first in the owner's project order, still held an ADR accept and a plan approval from 14:31 and a plant from 16:37 (from F240).

## Decisions
- **D7: under `softfield run`, a review hands its fixes to the main queue** (replaces D5, owner 2026-11-10 on F238: "planning responses and approvals don't wait"). After every round, `review_milestone` with `park` runs no queue of its own. A round with a stop `reason` records its stop as today. A round without one, its card's tickets left in `ready/`, finishes the review's row and returns PARKED with no stop recorded: F219 D3's exit, now taken for every fix, held or not. Back in `run_projects`, every project's requests and queued jobs go first, as for any job. Then the card's fixes go first among tickets, after the fast lane: a card whose review has rounds in `state.review_counts` and no stop in `state.review_stop` is under review (`under_review(state) -> set[str]` of short keys, in `runner/loop.py`), and `choose_ticket` takes its tickets right after the lane's. The week's pace line and Claude's limits hold them as any ticket. Their merges don't count toward a checkpoint (ADR 38: the next round reads them, so `_drop_covered_merges` covers `under_review` too). Once its tickets are done, `due_reviews` makes the review due again and it goes on from the next round. So nothing waits in place after a round, whatever is limited, and D5's wait is gone with its queue. `runner milestone` keeps today's inner queue.
- **D4: a limit inside a review's round parks it** (F53 D1 and ADR 16 item 4, for the whole round): under `softfield run`, a certain refusal parks the review's row until the reset, and an expired login parks it as `_park(login=True)` does any job. Its session is kept, no stop is recorded and no round is counted, and it goes on from that round, resuming its session. Developer tickets run meanwhile. `runner milestone` has no queue to go back to and keeps waiting.
- **D5 (replaced by D7, 2026-11-10): a job Claude can't take holds the review, not the factory:** under `softfield run`, the review's inner queue doesn't sleep for a limit, whatever is parked. A fix ticket left in `ready/` for a limit takes the exit F219 D3 built for one the week holds: the row is finished, PARKED returns, no stop is recorded and the review comes due again once its tickets are done. A last round (a stop `reason`) stops as F219 D3 has it, and the fix runs in the main queue. With no fix left, the review goes on, and `park_review` parks its next round if Claude is limited. The owner's pause still holds the inner queue.
- **D6: a repair Claude can't take doesn't wait:** refused by a certain limit or stopped by an expired login, `_repair_ticket` returns the ticket's problems, and its callers go on as they do when a repair fails.
- **D1: the round has three passes** (ADR 35 item 2 over ADR 30 item 6): first every project's fast lane (its lane tickets and their directions and escalations), then every project's queued jobs, then one ticket from the first project that has one, as today. The owner's pause holds the lane as it holds every ticket (ADR 35 item 5); the planner's jobs still run under it. Outside a pause they wait for the lane too: the owner kept ADR 35 as it is (2026-11-02, not taking up the lead's suggestion that replies go first).
- **D2: a lane escalation keeps its place:** the fast lane's ids (`first` for `dispatch.plan` and `dispatch.pick`) also take the tickets in `.softfield/tasks/escalated/` of a card in the lane, in `work_queue` and in `dry_run_plan` alike. `reserve_cards` keeps its meaning (the tickets that may use the reserve); the escalated ones join beside it.
- **D3: Next in line agrees:** a queued direction or escalation whose ticket id starts with a lane card's short key (`f172-06-…` for F172) shows in the Fast lane bay, its ticket in `ready/` or not. "A lane card" means the keys `_live_context` gives `fast_lane` (F192 D4, on main).

## Checked against main (lead, 2026-11-05)
- **Done elsewhere:** F219, Lead tickets follow Claude's week pace, did part of D5: a review whose lead fix the week holds returns PARKED (`_fix_held_by_the_week`). F192, A fast lane request shows on the board and Overview, landed the keys D3 uses.
- **Still true:** `project_round`, `reserve_cards`, the round's `call_claude` with no `park`, the inner `work_queue` with its wait and `_repair_ticket` are as these Decisions describe them. The ticket ids and D numbers are free.
- **`plan/f191` can't be approved until `f139-03-rebuild-clashing-plan-branches` lands:** F139's move gave this branch a move commit of its own, and it still branches from main of 29 October, so Approve sees 1,341 changed files, runner code included, and refuses them; catching up with main clashes too. That ticket, in the ready list, rebuilds such a branch at its next planner job.

## Plan
The stop goes first: it cost a day and more, the lane's order an hour.
- `f191-04-limit-in-a-round-parks-the-review` (lead, runner: D4).
- `f191-05-fix-ticket-holds-only-its-review` (lead, runner: D7, rewritten 2026-11-10 from D5), waits for 04.
- `f191-06-repair-doesn-t-wait-for-a-limit` (lead, runner: D6), waits for 05.
- `f191-01-lane-before-every-project-s-queue` (lead, runner: D1), waits for 05.
- `f191-02-escalated-ticket-keeps-the-lane` (lead, runner: D2), waits for 01 (both change `runner/loop.py`).
- `f191-03-next-in-line-lane-escalation` (developer, dashboard: D3), waits for 02.
- No mock-up: Next in line's Fast lane bay is F172's (`.softfield/cards/f172-mockup/goes-first.html`); an escalation only shows in the bay it was meant for.
