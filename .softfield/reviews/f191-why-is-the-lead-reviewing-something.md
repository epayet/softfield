# Review: F191, the fast lane goes first under softfield run too, escalations included

- **Status:** round 1 done, one finding, fixed in the round.

## Sign-off sheet

### 1. What changed
- **A review no longer stops the whole factory when Claude runs out.** If Claude refuses a review half-way through a round, or the login expires, the review waits in the queue until the reset. Developer tickets in every project keep running in the meantime. Then the review picks up the same round where it stopped. On 30 Oct this cost 28 hours with nothing running.
- **A review no longer runs its own fixes.** After a round, its fix tickets go to the normal queue. Your requests, the planner's replies and the other projects (coaster-ranker included) go first. Then the fixes run before any other ticket except the fast lane's. Once they are done, the review comes back for its next round. On 10 Nov, F9's review ran its fixes for three hours while coaster-ranker's approvals waited.
- **A fast lane card's escalation keeps its place in the lane.** The runner used to forget that an escalated ticket belonged to the fast lane. The Overview's Next in line now shows that escalation in the Fast lane bay too.
- **Fixing a broken ticket no longer waits for Claude.** When Claude is out of room or logged out, the repair gives up straight away, the same way a failed repair does.
- **The fast lane goes before every project's queued jobs** (f191-01). This landed earlier with F235.
- No mock-up for this card: the bay is F172's, and nothing new is drawn.

### 2. How to test it yourself
1. **Next in line on your phone:** wait until a fast lane card has a ticket escalated (it shows as "Escalation: f…" on the line). The escalation should appear inside the yellow Fast lane bay, not lower down.
2. **The next review with fixes:** on the Overview, watch a review that writes a fix ticket. The review should leave the line after its round. Requests you send right then (a plant, an approval) should be applied before the fix runs. The fix should then run before the other tickets, and the review's next round should follow it.
3. **The next time Claude's 5-hour window runs out during a review:** the review should show as waiting for Claude, and developer tickets should keep running. The review should continue by itself after the reset.

### 3. Left for later
Nothing new. The planner jobs' dollars on this card add up across a resumed conversation ($1.80 rising to $23.31). That is already planned as `f177-01-own-cost-per-job`.

### 4. Decisions waiting for you
None.

### 5. How the work went
- 2026-11-10, 12:24 to 12:28: f191-02 merged at the first attempt (Sonnet, $0.18). [Session](../sessions/2026-11-10-1210.md)
- 2026-11-10, 12:33 to 14:13: f191-03 merged on the local model's second attempt. The first attempt ran 70 minutes and was stopped for repeating itself. [Session](../sessions/2026-11-10-1232.md)
- 2026-11-11, 05:37 to 06:15: f191-04 (Opus, $1.41), f191-05 (Opus, $1.66) and f191-06 (Sonnet, $0.24) each merged at the first attempt. Sessions: [04](../sessions/2026-11-11-0548.md), [05](../sessions/2026-11-11-0610.md), [06](../sessions/2026-11-11-0620.md)
- 2026-11-11, from 10:47: review round 1. It found one gap in f191-03 and fixed it in the round.
- Lessons:
  - **A checkpoint reading only the test misses a mismatch with the spec.** f191-03's ticket said which cards count as in the lane, but the code used a narrower set. Its only test asked the card in *and* marked it, so it passed either way. The checkpoint called it sound. I fixed it and added the two missing cases.
  - **Moving work out of a job is better than teaching the job to wait.** D7 replaced D5's "don't sleep in the review's inner queue" with "no inner queue at all", and F219's special exit became the normal path. The diff got smaller and the tests got clearer.

### 6. What next
- **Product:** on hold, as you asked.
- **Factory:** watch the next two reviews that write fixes, to see whether the handover saves the hours it should. If round 2 often starts long after its fix merged (behind another card's fast lane), consider letting a card under review count as fast lane for its fixes.

### 7. What clogged the factory line
- **f191-03's first local attempt (70 minutes):** the model repeated itself on a 15-line change. The second attempt took 30 minutes. This is the known cost of slow-and-good, and nothing to unclog.
- **Overnight waiting (14:13 to 05:37):** f191-04 to 06 waited about 15 hours in board order. The line was busy, not stuck: 24 local developer jobs (12.7 hours) and 8 lead tickets ran in that time. None of F191's tickets hit a limit, failed, or stopped for you.

## What was built
- **`loop.lane_with_escalated`** (f191-02): `reserve_cards` plus the escalated tickets of a lane card. It is used by `work_queue` and by the dry run.
- **`queued_jobs(card_keys=…)`** (f191-03): a queued direction or escalation whose subject starts with a lane card's key goes in the Fast lane bay.
- **A round's `call_claude` with `park`** (f191-04): `_park` parks a review's row by milestone, and the round resumes from its session.
- **`loop.under_review`** and the handover (f191-05): with `park`, a round with no stop and its card's tickets in `ready/` finishes its row and returns PARKED. `choose_ticket` takes the fixes after the lane and any due parked ticket. `_drop_covered_merges` doesn't checkpoint them. `runner milestone` keeps its inner queue.
- **`call_claude(give_up=True)`** (f191-06): used by `_repair_ticket` only.

**Tests:** read closely, and sound. f191-04 drives a full `runner run` and checks four things: the refusal mid-round, a developer ticket running meanwhile, the same round resumed with its session, and the run counted once. f191-05 covers the pick order, the pace line, the dry run, the checkpoint and the owner's project order across `run_projects`. The edited tests (F219 D3's four) now run without `park`. That is right: under `park`, the handover replaced F219's exit, and a new test covers it with or without a held fix. The session report flags `test_overview.py` as edited for f191-03, but its diff only added a test.

No French changed: this is the factory, in English.

## Findings and resolutions
| id | severity | route | summary | resolution |
|---|---|---|---|---|
| F1 | should-fix | fixed | Next in line put a lane card's escalation in the bay only for a card asked in, not for one already in the lane | Fixed in round 1: one `lane_keys` set feeds `fast_lane` and `queued_jobs`. Two tests added: a marked card with no request, and a card asked out |

What held up when I looked for trouble:
- **A stopped review is never "under review":** every review that ends records a stop, and nothing clears `review_stop`. So an old card can't jump ahead of the board.
- **A last round's fixes:** with a stop, `under_review` drops the card. Its fixes run in board order and count toward a checkpoint, as ADR 38 wants.
- **A runner change from a fix:** a fix that changes the runner restarts the process from the main queue. The review has no stop, so it simply comes due again. The old `restart` stop isn't needed on this path.
- **A repair that gives up:** the job's row is finished as failed, nothing is left in flight, and no pause is recorded. The login item still reaches your desk.
- **A round with no fix:** the next round runs at once, and `park_review` still checks Claude's room before it.

Checkpoints: the one that read f191-03 called it sound. F1 is marked "missed": the narrower key set was visible in its diff, against the ticket's own words.

## What was set aside
Nothing.

## Workflow observations
- **How the flow went:** six tickets. Five (four in this list plus f191-01) were lead tickets and merged at the first attempt. One developer ticket took two local attempts. No stops, no limits and no interventions from you.
- **Models:** Opus was right for f191-04 and 05, which change the review loop. Sonnet was enough for 02 and 06.
- **What to change:** when a ticket's Context names an exact set to match ("the keys `_live_context` gives `fast_lane`"), its Done when should have a case that tells that set apart from a narrower one. This ticket's cases didn't. That is advice for whoever writes tickets, not a gate.

<!-- runner report -->
<!-- /runner report -->
