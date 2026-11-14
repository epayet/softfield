# F245: An approved card shows as Seed until the runner's next round

The planning thread behind F245's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-13 21:10

> I accpedfed a plan as go first but the milestone is not showing in the board at all for roller coaster app it's the title click thing why can't see
> Oh it went to seed for some reason

## The lead, 2026-11-13 21:12

> I found why M12 went to Seed and drafted a one-ticket fix for you to approve.
>
> 1. **Where M12 is now**: M12 on coaster-ranker, "Tap the title for a roller coaster ride across the sign", was built and reviewed while it showed as a Seed. You approved it with Approve first at 20:53. A developer built its ticket from 20:53 to 21:07, and Claude reviewed it from 21:07 to 21:10 and gave it 9. It is now in Ripe on coaster-ranker's board, under your desk's To sign off.
>    Action: Sign off M12 from its card when you've tried the ride.
> 2. **Why it went to Seed**: When you approve a plan, the runner updates the card's file on main to 'ready' and closes its thread. But it doesn't update the board's own stored copy of the card, which still said 'idea'. The board shows an idea card with no open thread as a Seed. The stored copy is only refreshed at the start of the runner's next round, and that came after the developer and the review had finished. So for about 17 minutes M12 sat in Seed while its ticket was being built. The board's rule is right; the copy it reads was out of date. This happens after every first plan you approve, on every project.
>    Action: Ticket f245-01: when the runner applies your requests, it also refreshes its copy of the cards, so an approved card is Planted (or first in the fast lane) before its first ticket starts.
> 3. **Approve it first?**: My recommendation is Approve first. It is one small lead ticket, a one-line change plus a test, so roughly the median 23 minutes. Every approval you make until then shows the same wrong Seed. If you approve it plainly instead, it goes last on the board, behind more than 100 ready tickets.
>    Action: Your choice: Approve first (recommended) or Approve.
> 4. **No mock-up**: There's no mock-up because nothing on the page changes. The card simply lands in the stage the board already meant to show.
>    Action: Nothing.
>
> Proposals:
> - F245: an approved card leaves Seed at once (plan)
