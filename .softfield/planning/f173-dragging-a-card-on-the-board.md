# F173: The board's order is the order the work runs in

The planning thread behind F173's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 19:38

> It works well but if a top ticket depends on another ticket, the other ticket needs to be prioritised and done first

## The lead, 2026-10-26 22:57

> I've drafted a fix on F173, The board's order is the order the work runs in: a ticket that a higher ticket waits for will take that ticket's place in the line. The new ticket passes pre-flight.
>
> 1. **Why it happens today**: When the top ticket is waiting on another one, the runner skips it and takes the next ticket it can run. The tickets it waits for still run in their own card's place on the board. Today's example: F15, Reprioritising tickets (place 4) needs f15-06-card-actions. That ticket waits on five others from F73 and F42 (place 6), F26 (place 7) and F63 (place 14). So all seven of F132's tickets (place 5) run first, and f63-01-desk-order runs near the very end.
>    Action: Nothing: the fix is the next point.
> 2. **The fix: a ticket that is waited for runs in the waiting ticket's place**: Each ready ticket takes the place of the first ticket waiting for it, whether that ticket waits directly or through others. Only the tickets that are actually needed move up, not the rest of their cards. Inside the moved group, the order still comes from what each one waits for. For F15, the runner would do f42-01 and f63-01, then f26-02, f73-01 and f73-02, then f15-06, and only then F132. Dragging a card still changes only the card's own place.
>    Action: Ticket f173-02-waited-for-goes-first (lead).
> 3. **Hidden cost: one top card can pull in a lot of other work**: Putting a card at the top now also brings forward every ticket it waits for, even from cards far down the board. F15 brings forward five tickets, about 2.5 hours at today's 32 minutes per ticket, all ahead of F132. That is what you asked for. The risk is that it looks like the board is being ignored. So Next in line will say why a ticket runs early: "early: f15-06-card-actions waits for it".
>    Action: Included in the same ticket (D7).
> 4. **No mock-up**: Nothing on screen moves. The only changes are the order of the line and a few words on Next in line for a ticket that runs early.
>    Action: Nothing.
>
> Proposals:
> - F173, part two: what the top ticket waits for runs first (plan)
