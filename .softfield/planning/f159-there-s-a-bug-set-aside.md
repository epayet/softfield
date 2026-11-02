# F159: A set-aside ticket says it won't run, with a Queue it button on its page

The planning thread behind F159's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-20 11:13

> there's a bug set aside, what am i supposed to do about it? i currently can't do anything with that

## The lead, 2026-10-20 11:23

> I drafted a plan on F159: a mock-up, one new ticket, and an update to bug-03 so that approving this plan also queues it.
>
> 1. **What the set-aside "bug" is**: It's bug-03-roadmap-items-to-seeds, first in the board's Seed column. It isn't a bug. On 13 Oct you asked for the old roadmap's open ideas to become seed cards so none stay buried in git. It sits under "bugs" because that's the only place a ticket outside a card can go. I wrote it into the set-aside folder that night and never asked you to queue it, so it has waited a week. Since then none of the roadmap's ideas has become a card. That was my mistake, not yours.
>    Action: This plan queues it (point 3).
> 2. **Why you can't do anything with it**: You're right. The board card opens the ticket's page, which shows the raw file, the state "later" and no button. The only Queue button is in the Set aside table on the Tickets page, and nothing points you there. F152 (A done card says where its review is, and set aside says it won't run) covers a card's set-aside tickets, which need nothing from you. This is the case where you do decide, so it gets its own small card.
>    Action: Ticket f159-01-set-aside-ticket-page (developer). A set-aside ticket's page starts with "This ticket won't run until you queue it" and a Queue it button, which sends the same request as the Tickets page's Queue button, so nothing changes in the runner. Pressed, the button shows on its way at once. The board card reads "Set aside, won't run until you queue it ›". The page shows the Goal and Done when as plain text instead of the raw file.
> 3. **bug-03 is queued when you approve this plan**: I updated it with what has changed since 13 Oct. `softfield init` is now built, the project cards F121–F137 exist, and F117 (While a developer job runs, say which part it is in) already covers one roadmap idea. That way it won't write those cards twice. It's one Opus lead ticket, about $1.60 going by the last week's lead tickets. At priority 90 it runs after most of the queue. Once it's queued you can drag it up on the board.
>    Action: Approving this plan queues it. Nothing else to press.
> 4. **The mock-up**: Today and Proposed use the real bug-03 card and its page. Proposed adds a Set aside panel at the top, with the hazard stripe and corner ticks, and a yellow Queue it button that turns into "on its way" when you press it. The ticket text is readable, and the lead's notes for the agent are folded away.
>    Action: f159-01 builds it as drawn.
> 5. **A Throw away button too?**: I'd leave it out for now. A set-aside ticket costs nothing while it waits. Removing one needs a new request in the runner, which means a lead ticket and more cost. The other set-aside tickets (five fix-ups on F9, Line polish, and one on F5, Steer from the phone) are kept on purpose, as a record.
>    Action: Choices: (a) no Throw away button, which I recommend; (b) a Throw away button beside Queue it, as one more lead ticket. Say b if you want it.
>
> Proposals:
> - F159: a set-aside ticket says it won't run, and you can queue it from its page (plan)
> - A set-aside ticket's page and board card, today and proposed (mockup)
