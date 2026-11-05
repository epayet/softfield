# F229: Remove the second bar with 4 chunks under every bar

The planning thread behind F229's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 11:03

> In every loading bar in overview allowance planning and board number of tickets there is a second unnecessary loading bar under it with 4 chunks

## The lead, 2026-11-05 11:34

> I drafted the removal as a one-ticket plan, and the mock-up comes with it. I couldn't open the mock-up in a browser from this job, so its switch hasn't been tried.
>
> 1. **You're right: it isn't a bar at all**: It's a decoration added by F81, Bring the factory theme to the older pages, meant as quarter marks under the bar. It shows no reading, but its pale chunks look like a second, empty loading bar. It appears in exactly the places you named: the Overview's allowance, Planning's lead window (twice) and the board's cards. It also breaks your rule that every bar says what it means, or goes.
>    Action: Remove it everywhere, with one developer ticket.
> 2. **Nothing replaces it**: I considered moving the quarter marks inside the bar and advise against it. The percent is already written beside every allowance bar and the tile's words, and each card says '4 of 8 tickets'. The mark that matters, where the factory stops, stays on the bar. Marks inside would be more clutter that nobody reads.
>    Action: One plain bar. The mock-up shows all three places side by side, using this morning's readings.
> 3. **One small thing has to stay**: The strip was also what kept the words off the bar, and the mark overhangs the bar by 4 px. Removing it alone would make the words touch the bar, so the bar gets 6 px of space beneath it. Board cards don't need this, because they are already spaced.
>    Action: This is in the ticket.
> 4. **It could come back by accident**: The mock-up of F219, Lead tickets follow Claude's week pace, still draws the strip, and f9-29 builds from that picture. If f9-29 merged after this ticket, it could copy the strip back in. The old test requiring the strip is replaced by one that fails if any template or the stylesheet names it, whichever ticket merges first.
>    Action: This is in the ticket; f9-29 itself stays as it is.
> 5. **When it runs**: Once approved, it takes its place on the board at the far end of the line, behind a long queue, so it could be a while. It's small, about half an hour of work like most tickets lately, and it shows on the pages you look at most.
>    Action: If it bothers you, drag the card up the board after approving. I wouldn't put it in the fast lane, since nothing is broken and Claude's windows are at 94% and 92%.
>
> Proposals:
> - F229 mock-up: one bar, without the strip (mockup)
> - F229: remove the strip under every bar, in one ticket (plan)
