# F249: A sent-back plan shows on its way on the desk and its thread

The planning thread behind F249's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-14 10:19

> A plan is being sent back but the answers wanted box is not orange dotted

## The lead, 2026-11-16 19:20

> I found the bug and drafted the fix as one developer ticket. Nothing is queued until you approve it.
>
> 1. **Why the box stays solid**: The desk draws a card's box dashed orange only when the lead owes it a reply. It counts a message you write on the thread, but not a Send back. So from your press until the runner's next pick, the box still says "the lead replied … ago". It stays solid and still counts as waiting for you. F133's plan shows it: you sent it back at 10:17 on Nov 14 and the runner picked it up at 10:19. Also, the plan you sent back drops out of the box, because the desk only lists proposals that are open or on their way.
>    Action: Ticket f249-01, below.
> 2. **The thread page has the same gap**: After Send back, your comments don't show on the card's thread, and nothing says the lead is writing, until the pick. A message typed on the thread does show at once. The rule is that what you ask for shows the moment you ask, so the same ticket fixes the thread page too.
>    Action: Same ticket.
> 3. **No mock-up**: Nothing new is drawn. The dashed orange box, the "being revised" words and the waiting message already exist. A sent-back plan now uses them, so there's no mock-up and no list of pages to photograph.
>    Action: Nothing, unless you want one.
> 4. **A developer builds it**: It's a small change to dashboard code that isn't protected, and the code already has an example to copy: how a waiting message is handled. That makes it developer work. It doesn't wait on any other ticket.
>    Action: Nothing.
>
> Proposals:
> - F249: A sent-back plan shows on its way at once (plan)
