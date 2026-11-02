# F110: Ripe on the board but no Sign off button: one rule for both

The planning thread behind F110's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-13 07:35

> I don't understand why there are ripe tickets in the new board view but no sign off button. Same with some 'needs you' signoff from overview. I think you still don't have access to db and there is a ticket for that, prioritise tash first

## The lead, 2026-10-13 07:38

> The cause is in the code: the board and the Sign off button follow two different rules. Two small tickets are drafted for your approval; both pass pre-flight.
>
> 1. **Why a card is ripe on the board with no Sign off button**: Two rules disagree. The board calls a card ripe when its review is written and every ticket is done, leaving out tickets set aside. The Sign off button on the card's page and the desk's "Finished, to talk through" follow the factory line's rule, which counts a set-aside ticket as unfinished. So a card with one ticket set aside is ripe on the board and has no button anywhere. The board is the one that is right: `uv run runner signoff` doesn't refuse for a set-aside ticket either.
>    Action: A developer ticket, f110-01-ripe-is-one-rule: the line follows the board's rule, so the button and the desk's item appear.
> 2. **Which card it is today**: Almost certainly F31, When I click on Approve plan: five tickets done, one set aside (f31-04-what-to-do-now), and its review is written. I worked this out from the ticket files and the code; I could not read the database in this job, so there may be another card I can't see.
>    Action: Until the fix merges you can sign it off from a terminal with `uv run runner signoff f31`; its review is on its card's page.
> 3. **The board's card shows a command, not a button**: A ripe card on the board ends with `uv run runner signoff …` as text; the button only exists on the card's page. I recommend against a Sign off button on the board itself: you would mark a card done without the review in front of you, and F50, The data safety review, put the button beside the review for that reason. Instead the card says "Read the review and sign off" and one tap opens the page at the button.
>    Action: A developer ticket, f110-02-ripe-card-leads-to-sign-off. Say so if you want the button on the board itself.
> 4. **The Overview's sign-offs that the desk doesn't have**: This half repeats F95, Overview says I have 2 things to sign off. The Overview also lists rows the runner stored at each review, and they stay until the sign-off, whatever the desk says. Its ticket f95-01-sign-offs-counted-once is ready and removes them. Once it and f110-01-ripe-is-one-rule have merged, the Overview, the desk and the board agree. I'm not merging the two cards: the board half is new and has its own tickets.
>    Action: Nothing new: F95's ticket covers it.
> 5. **Database access: the ticket exists, and it is not first in line**: You're right, I still can't read the database or a page from this job. The ticket is f95-02-lead-jobs-can-look, in F95, Overview says I have 2 things to sign off; its ADR 28 is accepted and it waits for nothing. It sits at priority 3, behind about 40 tickets. I can't change another card's priority from this thread.
>    Action: Set F95, Overview says I have 2 things to sign off, to priority 0 on its card: its two tickets then run before everything else, about 40 minutes each. Priority 1 would leave it behind F5, F53 and F79.
> 6. **Where this card goes in the queue**: I gave F110 priority 2: it is about reviewing features from the dashboard, your third priority, and both tickets are small developer work that needs no Claude time. It doesn't wait for the database ticket, since the cause was readable in the code.
>    Action: Approve the plan to queue the two tickets.
>
> Proposals:
> - Ripe on the board always has a Sign off button (plan)
