# F42: The space for me to scroll on a planning proposal card is very small

The planning thread behind F42's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-08 08:20

> The space for me to scroll on a planning proposal card is very small
>
> For example f17. Lots of sticky stuff meaning scrolling window small

## The lead, 2026-10-08 08:24

> I looked into it, and the page doesn't actually give you much room. On a phone, three things share the screen on the F17 review page:
>
> - the top bar stays pinned at the top and takes about 130 px;
> - the "Your review" box stays pinned at the bottom and takes about 175 px;
> - the F17 mock-up sits between them in a box 480 px tall that scrolls on its own.
>
> That leaves about 350 px, so you scroll a box inside a page and never see the mock-up whole. Inside that box the mock-up's scripts are also switched off, so you couldn't even try F17's "tap the dot" part.
>
> 1. **Why the space is small.** The three pinned or boxed parts above leave about 350 px of a 660 px phone screen. *Action:* the plan below.
>
> 2. **The mock-up opens full screen.** I'd fix the mock-up box first: it's the "small scrolling window" you saw. An "Open the mock-up" link shows it as its own page, at your phone's real width, with its scripts working. On a phone the link replaces the box. On a wide screen the box stays but grows as tall as the screen allows, with the same link. This doesn't loosen security: the mock-up page is already locked down so it can't send anything as the dashboard. *Action:* ticket f42-01.
>
> 3. **The "Your review" box becomes one row on a phone.** It keeps the count and the button side by side, about 60 px. Its title and its standing sentence go; the page already says the rest counts as agreed. The answer after you send still shows. *Action:* ticket f42-01.
>
> 4. **The top bar gets out of the way while you read.** On a phone it slides away as you scroll down and comes back as soon as you scroll up. I'd keep it pinned rather than let it simply scroll off, because the factory's status and Pause should stay one flick away. This changes an earlier decision (the bar has always stayed pinned), so it's flagged. Wide screens keep it as today. *Action:* ticket f42-02, which builds on F17's ticket, since that one already takes a row off the bar.
>
> 5. **The result.** Together these give the points about 560 px instead of about 350 on a phone. I've left the thread page's message box out on purpose: it holds a text field, so it needs its own look, best done together with F41. *Action:* nothing now.
>
> 6. **No repeat.** F17 makes the top bar shorter, which helps, but it doesn't touch the review page, the "Your review" box or the mock-up box. F41 and F30 are about the thread page's text, not its space. *Action:* nothing.
>
> 7. **No need to pause the factory.** Both tickets wait in `tasks/later/` until you approve, and nothing running is touched. *Action:* nothing.
>
> The plan is in `docs/milestones/f42-the-space-for-me-to-scroll.md`, and both tickets are drafts on `plan/f42`.
>
> 1. **Why the space is small**: On a phone the top bar (about 130 px) and the 'Your review' box (about 175 px) both stay pinned, and F17's mock-up sits in a 480 px box that scrolls on its own between them, in about 350 px. Its scripts are off inside that box too.
>    Action: The plan below
> 2. **The mock-up opens full screen**: An 'Open the mock-up' link shows it as its own page, at the phone's real width, with its scripts working. On a phone it replaces the box; on a wide screen the box grows taller and keeps the link. The mock-up page is already locked down, so nothing is loosened.
>    Action: Ticket f42-01
> 3. **The 'Your review' box becomes one row on a phone**: Count and button side by side, about 60 px; the title and the standing sentence go; the answer after you send still shows.
>    Action: Ticket f42-01
> 4. **The top bar gets out of the way while you read**: On a phone it slides away as you scroll down and comes back as soon as you scroll up, so the status and Pause stay one flick away. Wide screens are unchanged. This changes the earlier decision to keep the bar always pinned.
>    Action: Ticket f42-02, after F17's f17-01
> 5. **The result**: About 560 px for the points instead of about 350 on a phone. The thread page's message box is left for later, with F41.
>    Action: Nothing now
> 6. **No repeat**: F17 makes the top bar shorter but doesn't touch the review page, the 'Your review' box or the mock-up box. F41 and F30 are about the thread page's text.
>    Action: Nothing
> 7. **No need to pause the factory**: Both tickets wait in tasks/later/ until you approve; nothing running is touched.
>    Action: Nothing
>
> Proposals:
> - F42: room to read on the review page (plan)
