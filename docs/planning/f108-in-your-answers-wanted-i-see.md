# F108: Desk boxes say when: proposals and sign-offs show their time too

The planning thread behind F108's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-13 04:16

> In 'your answers wanted', I see when the lead replied (2 minutes ago for example). I'd like to see something similar for the other stuff like proposals (updated 3 minutes ago for example)

## The lead, 2026-10-13 04:19

> I drafted a plan for F108: one small developer ticket that puts a time on proposals and on cards to sign off. The ticket passes pre-flight.
>
> 1. **Proposals say when the lead proposed them**: Agreed, and it is cheap. A proposal's box will read "5 key points · proposed 3 min ago", written like the thread's "the lead replied 3 min ago". The desk already reads that time and only uses it to sort out your later requests.
>    Action: One developer ticket, f108-01-desk-says-when.
> 2. **"proposed" rather than "updated"**: I recommend "proposed 3 min ago" over your "updated 3 min ago". The time is that of the lead's reply that lists the proposal, and a later reply lists the whole set again whether or not a given proposal changed. "Updated" would then claim a change that may not be there. Say so if you prefer "updated"; it is one word in the ticket.
>    Action: In the ticket as "proposed".
> 3. **Cards to sign off say when they were reviewed**: "Finished, to talk through" has no time today either. Its box will read "reviewed 2 h ago · waits for your sign-off", from the end of the lead's review job. A card whose review was written in a terminal session has no such job and keeps today's words.
>    Action: Same ticket.
> 4. **A dashed box keeps its words**: Once you approve or reject a proposal, its box says "on its way · the runner applies it at its next pick", with no time. What is coming matters more there than when it was proposed, and the line stays short on a phone.
>    Action: Same ticket.
> 5. **Left out: seeds, "Didn't go through" and blocked tickets**: Seeds have no time stored: the card's doc holds only the day it was planted, and the dashboard's database doesn't hold even that. I'd not add a column for it. "Didn't go through" shows the runner's reason on its line, so a time there needs a change to the page; it is small, and I'll add it if you want it. The "Blocked tickets" group from F106, Where do blocked tickets go, isn't built yet, so its time belongs there.
>    Action: Nothing, unless you ask for one of them.
> 6. **It runs after the tickets that rewrite the same boxes**: f108-01 waits for f75-01-archiving-on-approval and f51-01-desk-counts-what-waits-on-you. They are the end of the chain of desk tickets from F63, I want to see cards in order, F74, One box per conversation, and F75, Archiving on approval, which all rewrite the same functions. The card stays at priority 100, so it goes after them anyway; lower it if you want it sooner.
>    Action: Nothing: it is in the ticket's depends_on.
>
> Proposals:
> - F108: desk boxes say when (plan)
