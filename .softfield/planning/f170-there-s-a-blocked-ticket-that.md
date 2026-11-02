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

## The lead, 2026-10-22 08:21

> Approved by the owner on 2026-10-22: approved plan/f170: queued f170-02-fix-after-try-again, f170-03-desk-offers-the-fix

## The lead, 2026-10-29 09:59

> Merged F190 here: A blocked ticket doesn't link back to the milestone /…

## The owner, 2026-10-29 09:59

> From F190, merged here:
> A blocked ticket doesn't link back to the milestone / original discussion and plans so the current blocked ticket f21 atm looks like I can't do anything about it

## The lead, 2026-10-29 10:02

> I've added the part that F170 didn't cover yet: a blocked ticket's own page will say why it is blocked, link back to its card and thread, and carry the same buttons as the desk. Nothing on main is touched.
>
> 1. **You're right: nothing on a blocked ticket leads back to its card**: f21-03 was blocked from 28 October 11:54 to 29 October 09:55. During those 22 hours the lead's fix ("Set aside f21-03, trim owner.md") was waiting on the thread of F21, The lead's briefs. On the desk, the blocked item linked only to the ticket's page. That page didn't say it was blocked or why, and had no buttons. Its one link back, F21-LEAD-BRIEFS at the top, opens the list of F21's tickets, not the card or its thread. The desk did say "the lead's fix waits on F21's thread", but that wasn't a link. f21-03 is sorted out now: approving F21's plan this morning set it aside, and nothing is blocked at the moment.
>    Action: Ticket f170-04, below.
> 2. **The blocked ticket's page gets a Blocked panel with the lead's fix and the buttons**: f170-04 adds a panel at the top of the page, built like the 'Set aside' panel the page already has: a hazard plate, the runner's reason in plain words, the lead's diagnosis and the name of its fix, then the desk's three buttons: "Approve the lead's fix" in yellow, "Try again as it is" and "Set aside" quiet. Under them are links to the card's thread and to the card's page. While the lead is still looking, the panel says so and shows only the quiet buttons. The desk and the page read the same facts through one shared function, so they can't disagree. The mock-up shows f21-03's page with its real words, Today and Proposed.
>    Action: Look at the mock-up; f170-04 (developer) builds it after f170-03.
> 3. **Every ticket's page names its card and opens the card**: The first link at the top of every ticket's page, not only a blocked one, becomes the card's name ("F21, The lead's briefs") and opens the card's page. Today it shows the card's long key and opens the list of its tickets. The Tickets page can still filter by card, so nothing is lost.
>    Action: Part of f170-04.
> 4. **F170 is last on the board, so this fix comes last**: F170 sits at the very end of the board, behind about 100 ready tickets. At roughly 20 minutes a ticket, that is more than a day of the line before f170-02 even starts. A blocked ticket is when you most need the right button, and it has hit you twice now (f132-01, then f21-03). I recommend dragging F170 up to just after F172, I'd like to be able…, which is first today. Its three remaining tickets are small and run unattended.
>    Action: Drag F170 up on the board when you next reorder.
>
> Proposals:
> - F170: a blocked ticket's page says why, links back and has the buttons (plan)
> - F170 mock-up: a blocked ticket's page (mockup)
