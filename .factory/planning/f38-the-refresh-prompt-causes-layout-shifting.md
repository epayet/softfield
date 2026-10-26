# F38: The new-version notice becomes a tag on the top bar, so no page moves

The planning thread behind F38's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:19

> Yeah that's the thing that suggest the refresh the page button

## The lead, 2026-10-26 23:05

> I found the bar you mean. It's the "New version of the dashboard: refresh" bar that `/version` draws at the top of every page, and it pushes the page down. The fix moves it onto the hazard stripe as a small tag, with a mock-up and one developer ticket.
>
> 1. **Which bar this is**: It's the "New version of the dashboard: refresh" bar. Every page asks the dashboard every 10 seconds whether its code has changed. When it has, that bar is put at the top of the page, above everything else, so the whole page drops by about 45 px while you're reading. That happens after any merge that touches the dashboard, which is several times a day.
>    Action: Move the notice into the top bar, as below.
> 2. **Top bar: on the hazard stripe, not in the top row**: Your worry about crowding is right. The top row already holds the logo, the status and Pause, the project picker and Light/Night. On a phone, one more item there would wrap onto a new line and move the page all the same. So the notice becomes a small yellow "↻ New version" tag at the right end of the yellow-and-black stripe. It sits on top of the stripe and takes no room, so neither the bar nor the page changes height. Tap it to load the new version. It doesn't blink.
>    Action: The mock-up shows Today and Proposed, on a wide screen and on a phone.
> 3. **Better still: you rarely see it**: My suggestion goes beyond what you asked. A dashboard left in another tab, or on a locked phone, loads the new version by itself, so when you come back it's already up to date. It never does this while you have a reply half typed or text selected (the same check the 5-second refresh already uses). A page you're looking at only shows the tag, so nothing changes in front of you. The cost is that a background tab may come back scrolled to the top.
>    Action: This is part of ticket f38-01. If you'd rather keep it to the tag only, say so.
> 4. **One small developer ticket**: f38-01 (about 30 minutes): it changes what the check returns and where it sits, adds the tag's style and the background-tab reload, and adds a test that the page doesn't move when the tag appears. It touches no protected files, so a developer can build it. On a phone, the top bar will hide while you scroll down once F42, The space for me to scroll on a planning proposal card, lands, and the tag will hide with it. That's fine.
>    Action: When you approve, f38-01 is queued in the board's order for F38.
>
> Proposals:
> - Mock-up: the new-version tag on the hazard stripe (mockup)
> - F38: no page moves when the dashboard updates (plan)
