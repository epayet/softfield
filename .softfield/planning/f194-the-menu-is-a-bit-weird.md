# F194: The menu: Overview, Planning, Board in fixed places, the rest in a sub menu

The planning thread behind F194's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-02 17:43

> The menu is a bit weird being horizontal scroll. The places of the items keep moving when going from page to page. There are 3 critical pages (maybe 4 with projects, but k suspect I won't at it _that_ often): overview, planning, board. Everything else could be accessible through a sub menu instead

## The lead, 2026-11-02 22:26

> I've drafted one ticket and a working mock-up: tap through the pages and watch where the items go. I couldn't open the mock-up in a browser from this session, so its layout is unchecked. The ticket's Done-when items test the real fit at 390 and 360 px.
>
> 1. **Why the items move**: It's built in, not a bug. There are ten tabs, and on a phone every page load scrolls the current tab to the middle of the strip (base.html, line 88, from 2026-09). So each item is somewhere else on each page. On a wide screen the Planning count going from 9 to 12 also pushes the tabs after it.
>    Action: The ticket removes that script and the sideways scroll.
> 2. **Your three pages, plus one slot for the rest**: Agreed. Overview, Planning and Board become fixed slots, and a fourth, More, holds Projects, Tickets, Jobs, Runs, Timeline, Agents and Bench. The slots have a set size, so neither the page nor the count moves them. On a phone they run edge to edge, 44 px tall. I'd put Projects in More as you suspected, first in its list. The cost is that Tickets and Jobs take two taps instead of one. The Overview already links to the job running now, so I think that's fine, but we keep no record of page visits to prove it.
>    Action: Build the Proposed of the mock-up.
> 3. **You still see where you are**: A sub menu can hide which page you're on. So on one of those pages the fourth slot turns yellow and reads its name ("Timeline ▾") instead of "More", same place and size. Each entry in the sub menu also gets a few words on what it is, which is a bolder draft for you to trim: Jobs and Runs are hard to tell apart by name alone.
>    Action: In the ticket. Say if you want the plain list.
> 4. **Where should the project picker go?**: This changes something you approved. In F132, One view of the whole factory: the top bar, the Overview, Jobs and the floor, the picker moves into the menu, in front of Planning, Board and Tickets. With Tickets in More that group is gone, and a phone's row has no room for a picker beside four slots. I recommend keeping it in the top row on every page and width (A), one fixed place, which suits what you asked for. The cost: it then looks as if it changes the whole page, while on factory-wide pages it will change nothing. The alternative (B) is in the menu on a wide screen and in the top row on a phone: it keeps F132's grouping, but the picker has two places and the code gets more fragile.
>    Action: The draft does A. Tell me if you prefer B.
> 5. **It runs after F132's picker ticket**: Both change the same lines of base.html, and I can't change another card's ticket from here. So this ticket waits for f132-08, then moves the picker back and keeps that ticket's crumbs. That wastes a small part of a local developer ticket, which is cheaper than the two colliding. F194 sits at the bottom of the board, behind 99 ready tickets, so about 5 days of work at the current pace. If you want it soon, drag it up: the wait pulls F132's two tickets forward with it.
>    Action: Drag the card up on the board after approving, if you want it sooner.
> 6. **A bottom bar on the phone? I'd say no**: A menu at the bottom would always be within thumb's reach, while today's top bar slides away as you scroll down. But it would take about 50 px on every page for good, and it would compete with the bottom of the planning pages and the review's phone bar. You already gave that space back to reading in F42, The space for me to scroll on a planning proposal card is very small. A scroll up brings the menu back, so I'd stay at the top.
>    Action: Nothing. Say if you'd like it drawn.
>
> Proposals:
> - F194: a menu of four fixed slots (plan)
> - F194 mock-up: the menu, Today and Proposed (mockup)

## The owner, 2026-11-02 23:06

> I sent back your proposal “F194 mock-up: the menu, Today and Proposed” (mockup-f194).
> - On its key point 1 (It works): I don't see anything in mock-up

## The lead, 2026-11-02 23:31

> The mock-up is fixed and sent back for you to read. The plan is unchanged and still waits for you.
>
> 1. **Why you saw nothing**: My mistake. I drew all four pictures with a script, and that script used a name the browser reserves (`top`). That stops the whole script before it draws anything, so the frames stayed empty. I told you it worked without having been able to open it.
>    Action: Fixed: the pictures are now plain HTML in the file, so they show even if a script fails. The script only moves the current page between them. I've noted the rule in my memory for later mock-ups.
> 2. **Still not opened in a browser**: This job can't run a browser, so I still haven't seen the pictures myself. I checked the cause by reading the code, and the pictures no longer rely on the script. The tapping could still have a fault of its own. If so, tell me what doesn't respond; you can judge the pictures without it.
>    Action: Look at the mock-up. Nothing else needed.
> 3. **The picker question still stands**: You hadn't seen the picture when I asked, so point 4 of my last reply is still open: the project picker stays in the top row on every page and width (my recommendation, and what the mock-up draws), or sits in the menu on a wide screen and in the top row on a phone. It changes what you approved in F132, One view of the whole factory: the top bar, the Overview, Jobs and the floor.
>    Action: The plan does the top row unless you say otherwise.
>
> Proposals:
> - F194: a menu of four fixed slots (plan)
> - F194 mock-up: the menu, Today and Proposed (mockup)
