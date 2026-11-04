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

## The lead, 2026-10-29 00:52

> Approved by the owner on 2026-10-29: approved plan/f38: queued f38-02-updated-note

## The runner, 2026-11-03 19:47

> f38-02-updated-note blocked: the finished work failed check-all; its work is on task/f38-02-updated-note.
> Its work is on task/f38-02-updated-note; its run's logs are in .softfield/var/runs/20261103-163949/f38-02-updated-note.
> What went wrong, and what is the fix? Propose it as a replan: the ticket reworked, split or set aside.

## The lead, 2026-11-03 19:50

> The work on f38-02 is good. It was blocked by a test outside it that failed by 1 millisecond. The replan mends that test first, then has the lead copy the finished work over.
>
> 1. **What went wrong: a test outside this work failed by 1 millisecond**: The "✓ Updated" note is finished on its branch, and 2975 of 2976 tests passed. The one failure is a runner test about Claude's reserve, nothing to do with the note. It expected a fake clock to stand still and found 12:00:00.001. The fake clock replaces Python's sleep for the whole test run, and Python's own subprocess code sleeps 1 ms while it waits for a program that hasn't ended yet. On a busy machine that nudges the clock. Python's source has exactly that 1 ms wait, which fits, but I can't run tests from here, so the new test in point 2 is what will prove it. A second reserve test failed the same way in the escalation's earlier full run, then passed alone and on the rerun.
>    Action: Ticket f38-03, in point 2.
> 2. **The fix: mend the fake clock itself**: The escalation suggested loosening the one assertion. I'd fix the fake clock instead, because seven assertions rely on it and each could fail the same way. With f38-03, Python's subprocess code gets the real sleep and the runner keeps the fake one. A new test runs a short program and checks the clock didn't move. It's a small change to one test file, so a developer can build it.
>    Action: New ticket f38-03-fake-clock-ignores-subprocess (developer, difficulty 2), first in this replan.
> 3. **f38-02 can't go back to a developer: the lead copies it over**: A developer ticket that comes back carries on from its branch. That branch now holds the escalation's note in `.softfield/developer.md`, which is protected, so the protected-paths check would refuse every attempt. As a lead ticket it starts again from main, and the runner keeps the finished work on a separate copy of the branch when you approve. The ticket tells the lead to make the same changes from that copy and not to rebuild or redesign anything. The cost is one more Claude job on work already done, probably a dollar or two (my guess; f38-01's escalation cost $1.40). Sending it back to the local model would be free, but it would have to undo that note, and it has already spent three attempts and 9 million tokens on this ticket.
>    Action: f38-02-updated-note comes back as a lead ticket, waiting for f38-03. What it builds and the mock-up don't change.
> 4. **Worth moving F38 up the board**: F38, The new-version notice becomes a tag on the top bar, sits at place 90, behind about 100 ready tickets at about 70 minutes each. That could be days. Until f38-03 lands, this 1 ms failure can cost any other ticket an attempt or a block, as it did here. I recommend dragging F38 near the top of the board once you've approved: the ticket is small and it protects everything behind it. If you leave it, nothing breaks, but the "Updated" note and the mend arrive later.
>    Action: Your call on the board. Nothing else is needed from you for this.
>
> Proposals:
> - F38: mend the fake clock, then the lead lands the "Updated" note (replan)
