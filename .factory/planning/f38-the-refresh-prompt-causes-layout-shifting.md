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

## The lead, 2026-10-26 23:51

> Approved by the owner on 2026-10-26: approved plan/f38: queued f38-01-new-version-tag

## The owner, 2026-10-28 14:09

> I've left the page open through a few tickets being done and haven't seen the new tag at all, doesn't seem to work

## The lead, 2026-10-28 14:12

> I couldn't find a fault in the tag itself. The likeliest reason you never saw it is that each page loads the new version by itself, without a word. So I've drafted a short "Updated" note that shows when that happens, and I need one answer from you to rule out a real bug.
>
> 1. **The tag is on main and the dashboard sends it**: f38-01 merged on 27 October. I asked the running dashboard directly whether there's a new version, as an out-of-date page would, and it answered "↻ New version". Since then, 14 merges have changed the dashboard, the last at 14:09 today (f143-02). The code, the check and the tag's style are all in place, and today's restyling (F81, the plate panels and buttons) didn't touch the tag.
>    Action: Nothing to fix in the tag itself.
> 2. **Why you most likely never saw it: the page updates itself without a word**: I added this to the plan, and the review made it stronger: a page you come back to (switching back to its browser tab, unlocking the phone, waking the laptop screen) checks for a new version straight away and reloads, unless you have text half typed. The tag only shows when the page is in front of you, visible the whole time, when a dashboard merge lands, and then only within about 10 seconds. If you came back to the page between tickets, it was already the new version each time, with nothing to tell you so. That is also how it can look like it doesn't work.
>    Action: D4 below: a page that reloaded itself says "✓ Updated" and the time, for 15 seconds.
> 3. **One question to rule out a real bug**: Was the page in front of you, on screen, the whole time it was open? Or did you switch tabs, lock the phone, or did the screen sleep? If it was on a laptop screen the whole time and a dashboard merge landed (most merges today were), the tag should have shown within 10 seconds. If it didn't, that's a bug and I'll look for it, starting with which page and browser you used. A quick test: keep the Planning page in front on the laptop until the next ticket merges.
>    Action: Reply with "in front the whole time" (I'll chase a bug, with the page and browser) or "I came back to it" (D4 settles it).
> 4. **"✓ Updated 14:09" after a reload the page started itself**: In the tag's place and shape, but in the panels' plate colours instead of hazard yellow, because it states a fact and there's nothing to press. It shows for 15 seconds, then goes without moving anything, and only after a reload the page started itself, not when you tap the tag. The alternative is to drop the self-reload and always show the tag for you to tap: simpler, but on a phone you'd come back to an old page every time. I recommend the note.
>    Action: Ticket f38-02-updated-note (developer, difficulty 2), building the mock-up's Proposed version. The sign-off for F38's first ticket can wait until this lands.
>
> Proposals:
> - Mock-up: "✓ Updated 14:09" on a page that updated itself (mockup)
> - F38, second round: a page that updated itself says so (plan)
