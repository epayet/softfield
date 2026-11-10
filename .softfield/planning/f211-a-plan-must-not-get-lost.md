# F211: Open plans survive a card's closing, and new ideas don't join a planned card

The planning thread behind F211's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-03 22:08

> A plan must not get lost when its card closes. Don't merge a new idea into a card whose plan is already approved unless that plan covers it; give it its own card. Sign-off and Archive must say when a plan is still open on the card, and let me keep it as a new card.

## The lead, 2026-11-04 01:02

> I traced how the plans got stuck and drafted a plan and mock-up: four tickets, which pass pre-flight. Nothing is queued until you approve.
>
> 1. **How the plans got stuck**: Three cases, from the database. F51, One box per card: F176 was merged into it after its plan was approved, and the lead's replan arrived at 00:54 on 29 October, three minutes after your Sign off, while your message was still waiting. F82, Text boxes grow: f82-02 was open when you signed off at 01:02, and the button said nothing. F195, the context window: archived with its plan open, though the card is still an idea. None of the drafts is deleted: the plan/ branches are still there and all three show under Set aside on Planning. But a signed-off card has no way forward: approving there would set a done card back to ready.
>    Action: Nothing to rescue: you already planted them again as F210, One box per card, F213, When live can't follow main, and F212, Bring back F195's tickets.
> 2. **The merge rule caused F51's case, so it changes**: The lead's brief says to keep the more advanced card, and that sent F176 into F51. New rule: a card with an approved plan takes a merge only when that plan already covers the idea, and the merge must name the tickets that cover it. Otherwise the idea stays its own card and the lead says which card it sits beside. On a signed-off card the lead draws no plan at all.
>    Action: Ticket f211-01.
> 3. **No runner check on the merge rule, and here's the alternative**: The runner can't tell what a plan covers, so this rule only lives in the lead's brief and the lead can get it wrong. The alternative is to hold every merge into a planned card until you press, which adds a desk item for each true repeat too. I recommend against it: the warning at Sign off and Archive catches a wrong merge before anything is lost.
>    Action: Nothing, unless you want the hold.
> 4. **Sign off and Archive say so**: A plate names the open plan, with Keep it as a new card as the yellow button, on the thread and on the card's page. Sign off and Archive anyway stay one press away, because stopping you isn't the goal. If you sign off and leave the plan, it stays on your desk with Keep available.
>    Action: Ticket f211-03; pictures 1 and 3 of the mock-up.
> 5. **A warning at Sign off alone wouldn't have saved F51**: When you pressed Sign off on F51, the plan didn't exist yet: only your message to the lead was waiting. So Sign off also says when a message is still waiting, and the plate at Archive catches the plan that arrives afterwards.
>    Action: Part of f211-03; picture 2.
> 6. **Keep is offered only on a closing card, which is narrower than you asked**: You asked for Keep on Sign off and Archive. I'd offer it only when the card is awaiting sign-off or already done. On a card that stays, like F140, Copilot checkpoints, the plan stays too and a message opens it again, so a new card would be a repeat. There you get one line by Archive saying so, and no button. Say if you want Keep everywhere.
>    Action: Picture 4.
> 7. **Keep plants a card and the lead drafts again, instead of moving the files**: Keep does what you did by hand on F210, F212 and F213: a new idea card with the plan's title, its key points and where the drafts are, and the lead queued on it. Moving the files automatically would break: tickets carry the old card's key in their names, and plan/f51 and plan/f82 start before the .factory to .softfield rename, so their diff against main runs to about 70 KB. Each kept plan costs one lead reply, and the plan comes back to you against today's code. The old branch stays, and deleting it is noted under Later.
>    Action: Ticket f211-02.
> 8. **A signed-off card's plan can't be approved any more**: The runner refuses and says why, and the plan's page shows Keep in place of Approve plan. Nothing relies on the old behaviour: no plan has ever been approved on a card already signed off. Set aside on Planning also marks those rows card signed off.
>    Action: Tickets f211-02 and f211-04; pictures 5 and 6.
> 9. **I couldn't open the mock-up in a browser from here**: This job has no browser, so I haven't seen it drawn. The pictures are plain HTML and the script only flips Today and Proposed, so a script error wouldn't blank them.
>    Action: If it looks wrong, tell me here.
>
> Proposals:
> - A plan still open: Sign off, Archive, its page and Set aside (mockup)
> - F211: open plans survive a card's closing, in four tickets (plan)

## The owner, 2026-11-04 10:05

> If I close a planning thread it is usually because I don't want the plan to be done. Agreed on new ideas not joining planned cards that are already approved. But if 2 open discussions (not archived) can be merged that would make sense

## The lead, 2026-11-04 10:09

> I revised the plan and mock-up for your answer: closing a thread now counts as a no, and merges stay between open discussions. All four tickets still pass pre-flight.
>
> 1. **Closing a thread now counts as no**: Archive stays one press and keeps its name, and I dropped the yellow plate and Archive anyway from my last draft. One line beside it names what it closes: 'Also closes the open plan: <title>. It won't be built unless you reply here.' Anything already archived shows nothing, because you've answered it.
>    Action: Tickets f211-03 and D4 in the card; pictures 3 and 4 redrawn.
> 2. **The lead must not bring a closed plan back either**: This already went wrong today. The lead merged F212, Bring back F195's tickets, into F195, the context window, whose thread you had closed on 2 November. That reopened it and cost a reply, and you closed it again at 08:04. The lead couldn't have known, because its list of threads doesn't say which are closed. Its prompt will now name them, and it won't merge with them, raise their plans or reuse their drafts unless you ask.
>    Action: Ticket f211-01.
> 3. **Open discussions merge, and the runner holds merges with closed threads**: Two open discussions with no approved plan merge as they do today. The runner can tell whether you closed a thread, so it holds any merge with one for you instead of applying it. This changes what I told you last time: there's still no runner check on whether a plan covers an idea, because it can't judge that, but it can check this.
>    Action: Ticket f211-01.
> 4. **Keep one exception: an approved plan that already covers the idea**: You agreed new ideas don't join approved cards, and your first note allowed one case: when the plan covers the idea. It's worth keeping. This morning F218, the developer's blue highlight, joined F209, The board lights the card at work. F209's plan already says a developer's card stays blue, so a separate card would have repeated its work. The lead must now name the tickets that cover the idea.
>    Action: Ticket f211-01. Tell me if you'd rather have no exception at all.
> 5. **'Usually' isn't always, so Keep stays on signed-off cards**: You closed F51, One box per card, and F82, Text boxes grow, at 09:47 on 29 October, then planted their plans again as F210 and F213. Those closes weren't a no: you hadn't seen the plans. Sign off therefore keeps its yellow warning, because signing the work says nothing about the plan. On a signed-off card a plain Keep sits beside Archive. On any other card there's no Keep.
>    Action: Pictures 1 and 3.
> 6. **Archive still deletes nothing**: I could make Archive remove the drafts as Reject does, since you mean no. I recommend against it: Reject also removes a card with nothing built, and you've changed your mind on closed threads before. A reply can still reopen one. Reject stays the way to get rid of a plan for good.
>    Action: Nothing.
> 7. **Closed threads with an open plan stay under Set aside for now**: A thread's Archive also lands under Set aside on Planning, though you meant no: F195 and F213 are there now. Separating them means a new kind of archive across several pages, and that list doesn't count as waiting for you, so I left it and dropped the 'card signed off' mark from my last draft. Picture 6 is gone and f211-04 is smaller.
>    Action: Noted under Later in the card. Say if the list bothers you and I'll add a ticket.
> 8. **I couldn't open the mock-up in a browser from here**: I still haven't seen it drawn, this revision included. The pictures are plain HTML and the script only flips Today and Proposed.
>    Action: If it looks wrong, tell me here.
>
> Proposals:
> - A plan still open: Sign off warns, Archive only names it (mockup)
> - F211: closed threads stay closed, and open plans survive a sign-off, in four tickets (plan)

## The lead, 2026-11-05 08:20

> Merged F223 here: Asked: the owner signed off F149, Retire the backlog file, did not remember whether they had asked it for more work, and wants to know what happens in that situation.
> Answered for F149: they asked on 2026-11-04. ADR 43 was accepted and its plan approved that day, and the sign-off was on 2026-11-05 with no message waiting. The work is f164-07-review-fixes-are-quoted-too, ready on F164, not started, and waiting for f164-01 and f164-03.
> Still to answer, from the code: `owner.signoff` refuses only when the card's own tickets are ready or stopped. Tickets on another card carry on untouched. A message still waiting doesn't stop a sign-off, and the lead still answers on the thread while the card stays done. An open plan doesn't stop one either. Approving a plan after sign-off sets the card back to ready, its tickets run, and `due_reviews` skips a signed-off card, so that work gets no review.
> Still open, the gap for F211's plan: an approved plan whose ticket sits on another card fires neither F211 warning. The only trace is the 'queued f164-07' line on the thread. Suggested fix: one line by Sign off and on the done card's page naming that ticket, its card and whether it has run, added to f211-03 and its mock-up.

## The owner, 2026-11-05 08:20

> From F223, merged here:
> I've signed off f149 but I don't remember if I asked it to do some more work. Clarify what happens in this situation

## The lead, 2026-11-05 11:05

> F149's sign-off lost nothing, and I've added the gap your question exposed to the plan and mock-up: a fifth ticket, with all five passing pre-flight.
>
> 1. **What happens when you sign off with more work asked for**: It depends on where the work is. Approved tickets on the card itself: the Sign off is refused, 'work is left'. Approved tickets on another card: they carry on and the sign-off doesn't touch them. A plan you haven't approved yet: it stays open on a card that can no longer use it, and nothing warns you. A message of yours still waiting: the lead still answers it, and nothing warns you there either.
>    Action: F211, Open plans survive a card's closing, adds the warnings for the last two, and point 3 covers the second.
> 2. **On F149, Retire the backlog file, you did ask for more, and it's safe**: On 4 November you asked to plant a review's small fixes from the review. You accepted ADR 43 and approved its plan that morning, then signed off on 5 November. The work is one ticket, f164-07, review fixes are quoted too, on F164, Plant a review's ideas straight from the review. It's queued and hasn't started, because it waits for that card's plates.
>    Action: Nothing. Drag F164 up the board if you want it sooner.
> 3. **Sign off will say when approved work sits on another card**: None of F211's warnings would have fired on F149: no plan was open and no message was waiting. So a line by Sign off will read 'Also asked for here, still to come: f164-07, on F164. Signing off doesn't touch it.' On the thread page it stays after sign-off until the ticket is done, so you can still check later. It's one line rather than a warning, and Sign off stays yellow, because you have nothing to do. It reads what your approval already recorded, so nothing new is stored.
>    Action: Ticket f211-05; picture 6.
> 4. **This case is rare, so f211-05 is the one to drop if you want less**: Only two approved plans have ever queued a ticket outside their own card: F149's, and F159, A set-aside ticket page, whose extra ticket was a bug. Bug tickets have no card, so they stay out of the line. I'd still build it, since it's a small developer ticket and it answers exactly what you asked. The alternative is to ask on the thread when you're unsure, as you did here.
>    Action: Say so here if you'd rather drop f211-05. Otherwise it stays in the plan.
> 5. **I couldn't open the mock-up in a browser from here**: I haven't seen the new picture drawn either. It's plain HTML like the others.
>    Action: If it looks wrong, tell me here.
>
> Proposals:
> - A plan still open: Sign off warns, Archive only names it (mockup)
> - F211: closed threads stay closed, and open plans survive a sign-off, in five tickets (plan)

## The owner, 2026-11-05 23:32

> I sent back your proposal “F211: closed threads stay closed, and open plans survive a sign-off, in five tickets” (f211-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-05 23:34

> I checked the plan against main: nothing in it is taken or done. I made one change, and the five tickets pass pre-flight.
>
> 1. **Nothing to renumber or drop**: No ticket numbered f211-01 to f211-05 exists anywhere else. Main hasn't built any of this plan's work since the plan was drafted. Every function the tickets name is still there.
>    Action: Nothing.
> 2. **One update: a kept plan keeps its card's area**: Since F171, Duplicated tickets on the board, a note planted without an area takes the project's area. Keep plants a new card, so a product card's plan could have landed as a factory card. f211-02 now gives the new card the old card's area, and the card's D5 says so.
>    Action: Ticket f211-02 updated.
> 3. **The examples still hold**: f164-07, review fixes are quoted too, is still waiting. So F149, Retire the backlog file, is still the case f211-05's line would show today.
>    Action: Nothing.
>
> Proposals:
> - A plan still open: Sign off warns, Archive only names it (mockup)
> - F211: closed threads stay closed, and open plans survive a sign-off, in five tickets (plan)

## The owner, 2026-11-10 11:47

> I sent back your proposal “F211: closed threads stay closed, and open plans survive a sign-off, in five tickets” (f211-plan).
>
> Check this against main as it is now: renumber what is taken, drop what is done or gone, and update the tickets.

## The lead, 2026-11-10 14:24

> I checked the plan against main as it is now: nothing in it is taken or done, and I updated two tickets for main's changes. All five tickets pass pre-flight.
>
> 1. **Nothing to renumber or drop**: The ticket numbers f211-01 to f211-05 are all still free. Nothing built since the plan was drafted does any of its work, and every function and page part the tickets name is still on main.
>    Action: Nothing.
> 2. **f211-02: a signed-off card is refused before anything touches its branch**: Since F139, Move the factory folder to .softfield, approving a plan first brings its branch up to date with main, then refuses one that clashes and asks you to press Refresh against main. For a signed-off card that would be the wrong advice: the old F51 and F82 branches all clash, and Keep drafts the plan again on today's code anyway. So the refusal on a signed-off card now comes first, and it also covers F224, Approve a plan to go first in line.
>    Action: Ticket f211-02 and the card's D8 updated.
> 3. **f211-04: the plan's page offers only Keep on a signed-off card**: Two new things sit by the approve button on a plan's page: the 'Refresh against main' line from F139, and F224's Approve first, which isn't built yet. On a signed-off card both give way to Keep, so the page never offers an action the runner would refuse.
>    Action: Ticket f211-04 updated.
>
> Proposals:
> - A plan still open: Sign off warns, Archive only names it (mockup)
> - F211: closed threads stay closed, and open plans survive a sign-off, in five tickets (plan)
