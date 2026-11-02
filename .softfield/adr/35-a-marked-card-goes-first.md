# ADR 35: The fast lane

- **Status:** Accepted (by the owner, 2026-10-29)
- **Date:** 2026-10-27
- **Deciders:** project owner (accepts), Claude (drafts)
- **Amends:** [ADR 22](22-one-visible-queue.md) item 2 (the pick goes by kind: planner, escalation, direction, checkpoint, review, then tickets) and [ADR 34](34-a-card-may-use-the-reserve.md) (the mark's name, where its lever is, and the order).
- **Evidence:** F172 (owner, 2026-10-26: "when the flag is on, it takes priority even over planning and reviews"; 2026-10-27: "Let's call it fast lane and it goes before everything"). On 2026-10-26 Next in line held 41 planning jobs, a direction, a checkpoint and F68's review ahead of the first ticket. The owner marked F90, F142 and F173 between 2026-10-22 and 10-26; each still waited behind all of that.

## Decisions (⚑ = deviates from an earlier decision)
1. **⚑ ADR 34's mark is the fast lane.** The owner puts a card in the fast lane, or takes it out. Every page says "fast lane", and the card's header says `**Fast lane:** yes`. Marks already written as `**Reserve:** yes` become `**Fast lane:** yes` in the same change.
2. **⚑ The fast lane goes before everything.** Its cards' ready tickets, and the ready tickets they wait for, are the runner's next jobs. They go before planner jobs, escalations, directions, checkpoints, reviews, a parked ticket whose reset has passed, and every other ticket. A direction or escalation about one of them goes with it: it is that ticket's own work.
3. **Inside the lane, the board's order.** With two cards in the lane, the one higher on the board goes first, and a ticket it waits for goes in its place (F173).
4. **It uses both of Claude's reserves** (ADR 34 items 3 and 5, unchanged): the week's and the owner's 25% of the 5-hour window, with both switches off.
5. **Only three things hold it:** a dependency that can't run yet, a real Claude limit (a window used up, a refusal resting it), and the owner's pause. While the lane waits for one of them, the line carries on with the next job, so nothing stands idle.
6. **⚑ The lever is on the card's page under the board** (`/milestones/<key>`, where a tap on a board card lands), as a "Fast lane" row of its header. It leaves the planning thread. The board's cards and the Overview say "fast lane" too, and Next in line shows the lane on top.
7. **The lane empties by itself:** a card leaves it when its tickets are done, and its header loses the line at sign-off (ADR 34 item 4).

## Settled with the owner
- **Before everything** (2026-10-27), planning and reviews included (2026-10-26).
- **The name** (2026-10-27): "fast lane".

## Alternatives turned down
- **Before everything except the planner:** the owner's replies would stay quick, but on 2026-10-26 the lane would have waited behind 41 planning jobs.
- **The pause doesn't hold the lane:** then the only way to stop the factory for a talk would be to take each card out of the lane. The pause stays the owner's one stop.
- **The lever on each ticket:** a replan's new ticket would come out of the lane, and the owner would flip one lever per ticket instead of one per card.

## Consequences
- **Cost: your replies wait.** While the lane has a runnable ticket, planning-room replies wait behind it, about 32 minutes a ticket (the median of the last 20), so hours for a card with several. To talk sooner, pause: planning goes, the lane waits, and resuming carries on.
- **Cost: checks and reviews wait.** Checkpoints and other cards' reviews come after the lane. Nothing merges without its gates.
- `dispatch.plan` and `pick` take the lane's ticket ids (`first`); `_next_task` picks from them first.
