# F230: Queue rows squeezed into the number column, one word per line

The planning thread behind F230's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-06 11:56

> Cards in the queue wrap words weirdly, 1 word per line like
> Fast
>  lane
> goes
> before
> everything
>
> On mobile at least

## The lead, 2026-11-09 16:04

> I found the cause and drafted one developer ticket to fix it. The text lands in a column only 28 pixels wide, so it breaks on every screen, not just the phone.
>
> 1. **Why the words stack**: Each Queue row is laid out as two columns: 28 pixels for the ticket's number, then the text. The fast lane's label has no number, so its text goes into the 28-pixel column and breaks after every word. This happens on every screen; a phone only makes it easier to see. Queued jobs (planning replies, plants) have no number either, so their rows are squeezed the same way.
>    Action: One developer ticket: a row without a number takes the whole width.
> 2. **The fast lane's stripe went missing too**: A local-model fix (f81-12, which fixed invalid markup in the Queue) turned the fast lane's bay into plain list rows. It left the bay's styles behind unused, so the hazard stripe and the label's look were lost as well. The fix brings them back on the new rows and removes the unused styles.
>    Action: In the same ticket.
> 3. **No mock-up**: This brings back the look the fast lane already had (F172, The fast lane), so there is nothing new to draw. Ask if you want a Today / Proposed picture anyway.
>    Action: Nothing.
> 4. **Small enough for a developer**: The ticket changes styles and one template, and follows the browser test already in the floor's tests. It includes a test that checks the label fits on one line at phone width, so the bug can't come back unseen.
>    Action: Developer ticket, about one run.
>
> Proposals:
> - F230, Queue rows squeezed into the number column: one fix (plan)
