# F123: Projects page: drag projects into order, as on the board

The planning thread behind F123's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 04:19

> I've drafted the plan for F123, Projects page: drag to reorder: one developer ticket, plus a mock-up whose drag you can try in Proposed. The ticket passes the ticket check.
>
> 1. **The board's drag can come to the Projects page now**: Your note waited for the drag on the board from F15, Reprioritising tickets. That drag is finished (f15-04 and the replan after it are done). Only the Projects page changes: it sends the same order request as today, and the runner applies it the same way.
>    Action: One ticket, f123-01-projects-drag.
> 2. **Mock-up: the number boxes go, each project gets a grip and a ⋯**: Today is copied from the live page and its CSS, with your three projects. In Proposed each project is a plate showing its place (#1), with the board's grip ⠿ to drag it and its ⋯ for Top, Up, Down and Bottom. A moved project reads 'moved · was #3 · not sent yet', and the board's bar at the foot of the screen holds Cancel and Send. The drag works in the mock-up, so you can try it on your phone.
>    Action: Look at .softfield/cards/f123-mockup/projects-drag.html; the ticket builds its Proposed.
> 3. **After a send you can still move projects and send again**: Today the number boxes lock once you send, until the runner takes the order. The board lets you move cards again and send, and the new order replaces the one on its way. I recommend the board's way here too, so both pages behave alike. The runner already applies only the latest order. The 'on its way' edge also changes from today's orange to the board's dashed yellow, so it looks the same on both pages.
>    Action: In the ticket (D4). Say if you'd rather keep the lock.
> 4. **The drag code is copied, not shared, for now**: Sharing one script between the board and this page would mean changing the board's working drag code so it can also order a list of three projects. That would put the board at risk for little gain. The Projects page gets its own small script, copied from the board's with a comment saying where it comes from. If a third page ever needs drag, that's the time to pull it into one shared file.
>    Action: In the plan (D5); nothing else to do.
> 5. **A developer builds it**: It's small, no file it touches is protected, and it copies a pattern already in the code: the board's script and its browser tests. That matches your rule: developer first. F62, F132 and F103 also have tickets that touch this page, but in other parts of it, so they won't get in each other's way.
>    Action: Nothing.
>
> Proposals:
> - Projects page: drag to reorder (plan)

## The owner, 2026-10-27 08:07

> On point 2: what mockup, i don't see it. once again...
> On point 4: no lazy, make it shared for the obviously common logic. the list of projects will grow

## The lead, 2026-10-27 18:55

> You were right on both comments. I drew the mock-up last turn but listed only the plan, so it had no link. It's listed below as its own proposal. The plan now moves the board's ordering code into one script that both pages share.
>
> 1. **The mock-up: my mistake, and it is listed now**: I drew .softfield/cards/f123-mockup/projects-drag.html last turn but listed only the plan, so nothing linked to it. It's the same slip that started F152, A done card says where its review is, and set aside says it won't run. The runner-side fix is that card's ticket f152-02-every-mockup-is-listed: after a planner job, the runner lists any mock-up the reply forgot. That ticket is ready, number 25 in line. F165, A point that speaks of a mock-up opens it in one tap, then covers older mock-ups dropping out of the list. Until f152-02 lands, I list every mock-up as its own proposal.
>    Action: The mock-up is its own proposal below. Its drag works in Proposed, so try it on your phone. Nothing new to queue: f152-02 already fixes the cause.
> 2. **One shared ordering script for the board and the Projects page**: Agreed: copying would leave two copies to drift apart as more projects come. A new script, factory_dashboard/static/order.js, holds what both lists do alike: working out what is out of place, a move, the ⋯ menu's Top, Up, Down and Bottom, the drag with its drop line and edge scrolling, and the send. Each page keeps only what is its own: how a row looks, its words, and the board's stages. The grip, ⋯ and drop-line styles become shared classes too. The plan's D5 names each function, so both tickets build against the same thing.
>    Action: Ticket f123-01-shared-order-script, the lead's: it changes the board's working drag, and only the board's browser tests can show the board still works. Its done-when says every board test passes unchanged.
> 3. **The Projects page in two developer tickets**: f123-01-projects-drag builds the rows: each project a plate with its place (#1), and the 'on its way' marks shown on every row, with nothing locked. The number boxes stay for now. It needs nothing else first, so it can run while the lead's ticket does, and the line doesn't wait on the lead alone. f123-02-projects-drag then adds the grip, the ⋯, the bar and the send on the shared script, and removes the number boxes. Two tickets are numbered 01 because a planner job can't delete a file from the plan branch, and Approve queues every draft there. So the first plan's draft now holds the rows work instead of being queued twice.
>    Action: Three tickets in .softfield/tasks/later/, all passing the ticket check.
>
> Proposals:
> - Projects page: drag to reorder (mockup)
> - Projects page: drag to reorder (plan)
