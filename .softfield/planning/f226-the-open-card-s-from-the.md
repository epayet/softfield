# F226: Remove 'Open the card' from the board's ⋯ menu

The planning thread behind F226's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 11:03

> The 'open card's from the board 3 dots button is not useful

## The lead, 2026-11-05 11:24

> I agree with you: the plan takes "Open the card" out of the ⋯ menu, with a mock-up and one small developer ticket.
>
> 1. **You're right, it adds nothing**: "Open the card" goes to the same address as tapping the card itself. The template builds both links from the same place, and a test even checks that they match. It's been that way since F15, Reprioritising tickets, added the menu.
>    Action: Remove it from the menu. One developer ticket, about 33 minutes of work at the recent pace.
> 2. **The rest of the menu stays**: Top, Up, Down and Bottom are the way to move a card without dragging. Open its conversation is the one link tapping the card doesn't give you, and Set aside stays on seeds and sprouting cards. I wouldn't remove the whole ⋯ button: every card still needs it for its moves.
>    Action: Keep them as they are. If you meant the whole button, say so and I'll redraw it.
> 3. **Bugs and cards with no conversation**: For these, "Open the card" was the only action. Without it, their menu is just the moves and Close. The ticket also makes sure no empty gap is left under the moves.
>    Action: Covered by the same ticket and shown in the mock-up.
> 4. **The review's pictures won't show the menu**: The sign-off pictures of the board show the page with the menu closed, so they won't show this change.
>    Action: To check it at sign-off, press ⋯ on a card and compare it with the mock-up. No extra work planned.
>
> Proposals:
> - Remove 'Open the card' from the board's ⋯ menu (plan)
> - F226 mock-up: the board's ⋯ menu (mockup)
