# F265: Planning's top tiles refresh by themselves

The planning thread behind F265's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 07:27

> The factory now section in planning doesn't seem to auto refresh ?

## The lead, 2026-11-18 07:28

> You're right that it doesn't refresh. I've drafted a small fix: one card doc and one developer ticket, which passes the ticket check. Nothing is queued until you approve.
>
> 1. **You're right: the two top tiles never refresh**: On Planning, only Coming and Your desk reload every 5 seconds. The two tiles above them, The factory now and The lead's window, are outside that reload. So what's running, the "Writing now … min in" line, the replies in line and both gauges stay as they were when you opened the page. F19 (Will I need to refresh planning) left the tiles out of its reload on purpose but never said why. F32 (The 5-hour lead's window says when it resets) noted it and accepted it at the time.
>    Action: Fix it in F265 with one small ticket (point 2).
> 2. **The tiles ride on the desk's reload, with no extra request**: Every 5 seconds the desk already fetches the whole Planning page and keeps only its own part. The same fetch can also update the two tiles, the way the Overview updates Now, Queue and the allowance from one request. Adding a third reload of its own would mean one more request every 5 seconds, which F19 set out to avoid.
>    Action: Ticket f265-01-tiles-refresh (developer, small): it follows the Overview's example in the code.
> 3. **The tiles pause while you type, like the desk**: The reload waits while you're typing in the Plant box or scrolling, so the tiles can be a few seconds late then. That's the trade the desk already makes: a few seconds late beats a wiped note.
>    Action: Nothing.
> 4. **No mock-up**: Nothing on the page moves or looks different. The tiles show what they were always meant to show, kept current, so I didn't draw a mock-up.
>    Action: Nothing, unless you want one.
>
> Proposals:
> - F265, Planning's top tiles refresh by themselves (plan)

## The owner, 2026-11-18 07:30

> It's the same for the answers wanted the orange dashes stay even though it's been approved or archived since. Same with the lead reply. The lead replied already but the box was still orange until I refresh. Be careful of not disturbing current typing with auto refreshes

## The lead, 2026-11-18 07:33

> I found why the orange dashes stay. The desk does reload every 5 seconds, but it holds off for 10 seconds after any scroll, and coming Back to Planning counts as a scroll. When the hold ends, nothing catches up. I've added a second ticket that fixes this and still leaves your typing alone. Both tickets pass the ticket check; nothing is queued until you approve.
>
> 1. **Your desk does reload, but your scrolling holds it back**: Your desk already reloads every 5 seconds, and a page reload showed the right state, so the page had stopped asking. It holds every reload for 10 seconds after any scroll. On a phone you scroll the desk all the time to read it. Coming Back from a plan or a thread also counts as a scroll. Each scroll restarts the 10 seconds, so a desk you keep reading never refreshes. When the hold ends, nothing catches up: the next try is the next 5-second tick, and a new scroll holds that one too. I can't prove from the code alone that this is what you hit, so the fix starts by reproducing your three cases in a browser: approve then go Back, a reply landing while you scroll, and an archive.
>    Action: Ticket f265-02-live-parts-catch-up (lead, tested first).
> 2. **The fix: a shorter scroll hold, and an immediate catch-up**: The hold after a scroll drops from 10 seconds to 2 after you stop. That's long enough not to move the page under your finger. When a hold ends, or you come Back to the page, it reloads at once instead of waiting for the next tick. This lives in one place shared by every live page (Overview, board, threads), so they all get the shorter scroll hold. The immediate catch-up is wired on Planning and on threads for now; other pages can follow.
>    Action: In f265-02, decisions D5 and D6 in the card doc.
> 3. **Your typing stays safe, as you asked**: The holds that protect what you type stay as they are. Nothing reloads while a box has the cursor, holds text you haven't sent, or sits in an open fold, or while text is selected. The ticket tests this directly: a half-typed note in the Plant box survives every reload and every catch-up.
>    Action: Covered in f265-02.
> 4. **The lead tickets run first in the queue**: At about 48 minutes a ticket, the dashed boxes keep happening until these land, and they sit behind the rest of the queue as things stand. If they bother you daily, move F265 up the board once it's approved: there are two tickets, a small one for a developer and one for the lead.
>    Action: Nothing, unless you move it up the board.
>
> Proposals:
> - F265, Planning's top tiles refresh by themselves (plan)

## The owner, 2026-11-18 08:34

> the board tickets also don't refresh on the board page, i had to refresh the page

## The lead, 2026-11-18 12:20

> The board has the same cause as Planning. I've added a third ticket so the board catches up too; all three tickets pass the ticket check.
>
> 1. **The board has the same cause as Planning**: The board already checks for changes every 10 seconds. That came with F209 (The board lights the card at work and keeps itself up to date). It skips a check while you drag a card, have moves you haven't sent, or have the ⋯ menu open. It also skips while the page is holding for scrolling or typing, and the board shares Planning's 10-second hold after any scroll. On a phone you scroll the board all the time, sideways through the stages too, so nearly every check falls inside a hold. When the hold ends, it waits for the next 10-second check, which you may scroll through again.
>    Action: Fixed by f265-02's shorter hold (2 seconds after you stop) plus ticket f265-03 below.
> 2. **The board's "refreshes every 10 s" line was wrong while it was held**: The small line on the board's plate keeps saying "refreshes every 10 s" while scrolling or typing holds the board. Only moves you haven't sent and a dashboard that doesn't answer change those words. So the board told you it was fresh when it wasn't. With the fix, it reads "Refresh held while you scroll or type" until a check goes through.
>    Action: In f265-03.
> 3. **No mock-up for the board line**: It's one more wording state for a line that already exists, in its existing "not fresh" style. Nothing moves and there's no new colour or shape, so I didn't draw a mock-up.
>    Action: Nothing, unless you want one.
> 4. **F265 now covers every live page, not just the Planning tiles**: The card started with Planning's two top tiles. It now also covers your desk, threads and the board, because they share one cause. That's still one theme (live pages that stop following), so it stays one card rather than a new one. Other live pages, such as the Overview, get the shorter scroll hold too. Their immediate catch-up can follow later if you notice the same thing there.
>    Action: Nothing.
>
> Proposals:
> - F265, Live pages keep up by themselves: Planning, threads and the board (plan)
