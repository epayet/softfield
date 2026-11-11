# F242: A fast-lane card's review goes in the fast lane

The planning thread behind F242's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-11 18:36

> The review of a fast lane ticket doesn't seem to get prioritised as fast lane, runner went onto other things rather than the milestone review. Reviews are important as the lead can catch bugs

## The lead, 2026-11-11 18:44

> The fast lane only counts a card's ready tickets. When a card finishes its last ticket, its review falls back into the ordinary queue. I've drafted a two-ticket plan on `plan/f242`, and both tickets pass `softfield check-tickets`.
>
> 1. **What happened: F191's review ran 2 h 15 late**: This morning F191 (Why is the lead reviewing something) was in the fast lane. Its review was queued at 08:33. Claude was in your share of the 5-hour window, so the review was parked until 10:30. A fast-lane ticket would have run anyway, because the lane may use both reserves. Meanwhile developers ran f210-03 and then f77-02, which was still running at 10:30. The review only started at 10:47 and finished at 11:28. There are three causes. The lane is made of ready tickets, so a card with all its tickets done drops out of it. Parking a review ignores the lane's reserves. Reviews are queued one at a time in card order, so a fast-lane card's review can wait behind another card's review, checkpoint or escalation. The full timeline is in the card doc under 'What happened'.
>    Action: The plan below fixes all three.
> 2. **A fast-lane card's review goes with the lane**: A card marked fast lane stays in the lane until it is signed off, review included. Its review is queued before other cards' reviews. It runs before every planner reply, checkpoint and ticket, in every project's round. It is held only by its own card's checkpoint or escalation, and parked only by a real Claude limit, the same as a fast-lane ticket. Next in line shows it in the Fast lane bay. Cards out of the lane keep today's order.
>    Action: f242-01 (lead, runner) and f242-02 (developer, Overview), which waits for 01.
> 3. **The cost: a review can use your share of the 5-hour window**: A review round runs on Opus and costs about $1–3. If your card is in the fast lane, it can now use the 5-hour share the factory normally leaves you, as fast-lane tickets already do. I recommend this because putting a card in the fast lane already says 'spend the reserve on this', and a review is where the lead catches bugs. The other way is to let the review jump the queue while keeping the normal reserves. It would then still have waited until 10:30 this morning.
>    Action: Built as in point 2 unless you prefer the normal reserves.
> 4. **A running ticket is still never stopped**: The last 17 minutes of the delay came from f77-02, which was already running when the review became free to run. The runner never interrupts a running ticket, and this plan doesn't change that. A stopped ticket pays for its work twice.
>    Action: Nothing.
> 5. **No mock-up**: Nothing new is drawn. The review row already shows on Next in line, and it only moves into the Fast lane bay. F172's drawing (.softfield/cards/f172-mockup/goes-first.html) already shows that bay.
>    Action: Ask if you want a picture anyway.
> 6. **Put F242 high on the board**: F242 sits at priority 100, so once approved its tickets come after the 133 ready ones, which is days of work. If reviews matter now, drag F242, The review of a fast lane ticket, up the board after approving, or put it in the fast lane.
>    Action: Your drag on the board.
>
> Proposals:
> - F242: a fast-lane card's review goes in the fast lane (plan)
