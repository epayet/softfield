# F209: The board lights the card at work and keeps itself up to date

The planning thread behind F209's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-03 20:12

> i want the ticket currently being worked in the board be highlighted a bit more. also it doesn't seem to auto refresh very well

## The lead, 2026-11-03 20:17

> The mock-up and a three-ticket plan are drafted. Nothing is queued until you approve.
>
> 1. **Why the card at work is hard to spot**: Tonight 16 of the 53 planted cards have the same orange edge, because that edge means a ticket has ever started. The card at work differs only by one small "Now:" line, and it can sit far down the column: F9, line polish, is #23.
>    Action: Give it a thick frame and a filled "Working now" head, in its usual place. Orange means the lead and blue means a developer, the same as the top bar's dot.
> 2. **A highlight alone isn't enough**: You asked for "a bit more", but even a bright frame doesn't help when the card is 22 cards down on a phone. I wouldn't move it up the column, because the board's order is the only order. Your rule that what's running comes first points to something on the first screen.
>    Action: Add a plate above the plots saying what works now, on which card, for how long and at what place in the line. Tapping it opens the card. It is a ticket of its own, so you can drop it. If the look is too loud, the mock-up also shows a calmer card.
> 3. **Reviews and your conversations light up too**: You said tickets, but a review or the lead answering you is also work on a card, and today neither is lit. I'd light any live job on its card. A job held by Claude's limit isn't lit and says until when.
>    Action: Included in the first two tickets.
> 4. **The board doesn't refresh at all**: The page is drawn once. Only the top bar updates every 5 s, so it can name a ticket the board doesn't show yet. The whole page reloads only when the dashboard's own code changed, which is why it sometimes looks fresh.
>    Action: The board fetches itself every 10 s and swaps only what changed, including the plot counts. It stops while the page is hidden and fetches at once when you come back. I chose 10 s rather than 5 because it fetches the whole page and a ticket takes about an hour.
> 5. **This reverses a decision on F192**: F192, A fast lane request shows on the board, decided that the board doesn't poll because polling would fight a drag. The refresh answers that by holding during a drag, the ⋯ menu, moves not sent, a half-typed search or a recent scroll. The plate says when your moves are holding it, and when the dashboard doesn't answer. F192's plate on a card will then update on its own too, and its tickets don't need to change.
>    Action: Approving this plan replaces that decision. F192's back-button ticket and this one share the same redraw function, and either can land first.
> 6. **Where it goes in the line**: Once approved, the card joins the end of Planted. That is three tickets at about 66 minutes each, behind 53 cards.
>    Action: If you want it sooner, drag it up on the board. All three tickets go to developers: they are unprotected and follow existing code.
>
> Proposals:
> - The card at work stands out, and the board follows the work by itself (plan)
> - F209 mock-up: the card at work on the board (mockup)
