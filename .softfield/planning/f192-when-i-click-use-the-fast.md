# F192: A fast lane request shows on the board and Overview as soon as it's made

The planning thread behind F192's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-02 17:43

> When I click use the fast lane and it's being queued for pick up, I want to see it already when I go back to the board

## The lead, 2026-11-02 22:19

> This drafts a small plan with a mock-up: the board and the Overview show a fast lane request as soon as you make it.
>
> 1. **Why you don't see it today**: Only the lever on the card's own page knows about your request. The board's plate reads the card's doc, and the runner writes that at its next pick. F170's request of 30 October was only taken on 2 November, so for three and a half days the board showed nothing.
>    Action: Ticket 01 puts a dashed plate on the card: "fast lane · on its way · at the runner's next pick". Turning it off shows "leaving the fast lane · on its way".
> 2. **The back button needs its own fix**: You said "when I go back". A phone's back button can bring the old page back from memory, and the board doesn't fetch itself again, so the new plate alone could still leave you looking at the old board. I read this from the code and haven't reproduced it on a phone.
>    Action: Ticket 02 makes the board redraw itself when you arrive by back or forward. If you have moves not yet sent, it leaves them alone.
> 3. **I'd go further than the board: the Overview too**: You asked for the board, but your rule is that a request shows wherever its result will appear, and the Overview's "Fast lane:" line and Next in line are two of those places. Next in line can show the tickets in the lane's bay straight away, because the runner takes requests just before it picks.
>    Action: Ticket 03, which can run or be dropped separately from the other two. If you only want the board, reject it in your comments and I'll remove it.
> 4. **The mark goes on the plate, not the card's edge**: A card's dashed edge already means a sent reorder is on its way, and both can be true at once. A dashed plate keeps the two apart. A board you leave open keeps showing the plate until its next load, as a sent order does today, because refreshing it live would fight a drag.
>    Action: Drawn in the mock-up, with Today and Proposed on real cards: .softfield/cards/f192-mockup/lane-on-its-way.html.
> 5. **Where it lands in the line**: Once approved, it joins the bottom of Planted, behind 54 cards. It's three small developer tickets. All three change only the dashboard, so nothing in the runner changes.
>    Action: Drag it up the board if you want it soon; I'd put it just after F170, Blocked tickets.
>
> Proposals:
> - A fast lane request shows on the board and Overview as soon as it's made (plan)
> - F192 mock-up: a card on its way into the fast lane (mockup)
