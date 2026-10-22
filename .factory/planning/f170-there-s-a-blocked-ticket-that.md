# F170: Blocked tickets: give the tests 30 minutes, and put the lead's fix on the desk

The planning thread behind F170's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-21 22:27

> There's a blocked ticket that I keep trying to approve and it keeps coming back I don't get it. What am I supposed to do with this, why doesn't it just work

## The lead, 2026-10-21 22:38

> I've drafted the plan for F170: three tickets, with a mock-up for the desk change. Nothing on main is touched.
>
> 1. **Why it keeps coming back: two tickets, one cause the button can't fix**: Two tickets were blocked today, both for the same reason. f132-01 was blocked at 15:56 and f152-01 at 22:25. In both, the code was fine. The full test suite now takes about 19½ minutes and the runner stops it at 20, so it was cut three times on each ticket. That cost about 3.5 hours of the line and about $2 of Opus per ticket. "Try again" puts the ticket back exactly as it was, so it hits the same 20-minute wall. That is what you pressed on f132-01 at 21:23. The ticket is back in the queue (3rd in line) and would be cut again. The escalations raised the limit too, but only on their own branches. The runner reads its settings once at start-up, so neither raise ever reached it.
>    Action: The fix is ticket f170-01 (point 3).
> 2. **Why approving didn't work either**: The lead had already written the real fix on F132's thread ("F132: raise the test time limit, then land f132-01 from its branch"). When you pressed Approve at 21:46 it was refused with "plan/f132 clashes with main". Try again had just put f132-01 back in the queue, and the plan wanted to put its own version of the same file there, so the two collided. f152-01's fix on F152's thread depends on that F132 ticket, so it can't land either. Neither failure was yours: the yellow button on the desk was the wrong one to offer, and pressing it broke the right one.
>    Action: Tickets f170-02 and f170-03 (points 4 and 5).
> 3. **The fix now: the tests get 30 minutes, ahead of every other ticket**: f170-01 is a lead ticket at priority 0, so it runs before anything else in the queue. It raises the test limit from 20 to 30 minutes, gives the developer's shell the same 30, and makes the runner pick up a settings change on main without a restart. It replaces the F132 and F152 fixes, so leave those two proposals alone: if you approve either, it will be refused. Once f170-01 is merged, f132-01 passes as it is, since it's already queued. For f152-01, press "Try again" on its desk item. You can press it now: it waits behind f170-01. No pause is needed, as long as you approve this plan before the F68 review that is next in line finishes.
>    Action: Approve the plan below, then Try again on f152-01.
> 4. **Try again will no longer make the lead's fix unapprovable**: f170-02: if you press Try again and then approve the lead's fix, the fix replaces the ticket Try again put back, keeping its run history, instead of being refused as a clash. Any other clash is still refused.
>    Action: Ticket f170-02 (lead).
> 5. **The desk offers the lead's fix as the yellow button**: f170-03: a blocked ticket on the desk shows the lead's diagnosis and its fix inside the item. "Approve the lead's fix" is the yellow button, right there, so you no longer need to open the card's thread. "Try again as it is" becomes a quiet button, with a line saying it runs the ticket unchanged. While the lead is still looking, the item says so and there is no Approve button. A bug ticket (it has no card) keeps today's two buttons. The mock-up shows Today and Proposed with the real f152-01 item.
>    Action: Look at the mock-up; ticket f170-03 (developer) builds it.
> 6. **Risk: the fix's own check still runs under the old 20 minutes**: f170-01 is checked by the full suite before it merges, and that check still runs under today's 20 minutes, with the suite at about 19½. The ticket adds only fast tests, so it should fit. If it is cut anyway, re-queuing it would pay for the work twice. The quick way out is then a one-line settings change in a short terminal session, which I'd ask you for.
>    Action: Nothing unless it happens.
> 7. **This is the third time the limit goes up: the real fix is a faster suite**: The limit was 15 minutes on 10-13, then 20, and now 30, while the suite has grown from 12½ to 19½ minutes in eight days. Raising it again only buys time. Speeding up the suite is the job of F71, "I suspect we might need to increase the timeouts…" (its slow-tests study; your F168 note was merged into it this evening, and the lead is answering there now). I also considered a rule that a test run cut for time blocks nothing, and turned it down for now. It would change the escalation limits, so it needs an ADR, and a faster suite makes it unnecessary. One overlap to watch: if F71's reply also proposes raising the limit, approve only this card's version. It goes first and also makes the runner pick up the change without a restart.
>    Action: Nothing here; F71 carries the suite's length.
>
> Proposals:
> - F170: the tests get 30 minutes, and a blocked ticket's fix is one press (plan)
> - F170 mock-up: a blocked ticket on the desk offers the lead's fix (mockup)
