# F264: The factory should never stay idle. The pacing and reserve…

The planning thread behind F264's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-18 07:22

> The factory should never stay idle. The pacing and reserve are to balance local and remote work. If there is lead work available and tokens available and no developer work available, the lead should work. If pacing or past reserve line, developer work should be prioritised. I see the factory is not doing anything ATM

## The lead, 2026-11-18 07:26

> Today the line has done no ticket work since 02:04. Claude's week is 34% used against a pace line of 26%, so the pace holds all 101 ready lead tickets until about Thu 01:36. All 40 developer tickets wait on one of those lead tickets. I've drafted ADR 49 and two tickets to fix this. One ticket check came back with "accept ADR 49 first", which is expected because the ticket relies on it.
>
> 1. **Why the factory is doing nothing**: The last ticket job ended at 02:04 (a review). Since then only planning and usage readings have run. Claude's week is 34% used and today's pace line is 26%, so the rule from ADR 44 (Lead tickets follow the pace line) holds all 101 ready lead tickets 'until about Thu 01:36'. That's about 23 hours idle. The rule does let developer tickets run, but every one of the 40 ready developer tickets waits on a lead ticket that hasn't run yet. So the pick finds nothing and the local model sits unused, with about $112 of the week still under the 70% mark.
>    Action: Fixed by ADR 49 and f264-01 below.
> 2. **I agree, and it partly reverses what you asked for on 4 Nov**: On F219 (Lead tickets follow Claude's week pace) you chose 'the pacing and the reserve' over 'stop at 70%'. Your new rule keeps the pace as a priority and the 70% mark as the stop: over the pace line, developer tickets go first, and the lead runs only when no developer ticket can start. I think that's right. The lead's work is what gives the free local model its work, so holding the lead holds both. Lead tickets also cost little: since 9 Nov they cost $57, against $284 for planning and $71 for reviews. The week has run out early every week because of planning, not lead tickets.
>    Action: ADR 49 items 1 and 3; it amends ADR 44 items 1 and 6.
> 3. **The cost: the 70% mark comes sooner**: At about $1.30 a lead ticket and $3.10 for each 1% of the week, a full day of the lead filling the gaps is about 25 tickets and 10% of the week. At this rate the week runs out on Sat 11:40. Filling the gaps brings the 70% mark closer, and after it lead tickets wait for the last 10% as they do today. Developers keep working through the tickets those lead tickets unblocked, and planning keeps its 30% reserve.
>    Action: Nothing more: the reserve still protects planning.
> 4. **How far the lead may go to fill a gap**: My recommendation is up to the 70% mark, so planning and reviews keep their 30% until the reset. In the week's last 10% the whole reserve opens to lead tickets, as it does today. The other choice is up to 100%: more lead work, but planning would stop before the reset in most weeks, as it did on Sat 14 Nov.
>    Action: ADR 49 item 2. Tell me if you want 100% instead.
> 5. **Which lead ticket fills the gap**: My recommendation is the next lead ticket in the board's order, since the board is your only order. The other choice is the lead ticket that frees the most developer tickets: that gets more local work out of each Claude dollar, but it means a second order beside the board's. You can get the same effect by dragging a card like F132 (The overview shows the whole factory) up the board.
>    Action: ADR 49 item 6 and the alternatives it turns down. Tell me if you prefer the unblocking order.
> 6. **Getting the line moving today**: f264-01 is itself a lead ticket, so the pace would hold it until Thu 01:36 like the rest. After you approve, put F264 in the fast lane so it goes first. To get work moving before then, turn on the 'use reserve' switch under the Claude week bar on the Overview. It turns itself off after 24 hours, and at about 10% of the week a day it stays well under the 70% mark.
>    Action: You: accept ADR 49, approve the plan, put F264 in the fast lane, and turn on the 'use reserve' switch if you want work today.
> 7. **The Overview's words change, with no mock-up**: The 'Over pace' plate under the Claude week bar now says 'lead tickets wait until about Thu 01:36'. It would say 'developers first; the lead takes over when they have nothing, up to the mark', and a held lead row would say 'goes when no developer ticket can'. Only the words of an existing plate change, so I didn't draw a mock-up. Ask if you want one.
>    Action: Ticket f264-02, a developer ticket.
> 8. **F250 (Tell the phone when the factory is done for the week) follows on its own**: F250 decides 'done' from the lead tickets Claude's week holds back. After f264-01, the week holds them back only at the 70% mark, so F250's notification will mean real idle time, not a pace wait.
>    Action: Nothing: f264-01 changes the function F250 reads.
>
> Proposals:
> - ADR 49: Over the pace line, the lead works when the developer has nothing (adr)
> - F264: the lead fills the gap (plan)

## The owner, 2026-11-18 07:57

> I sent back your proposal “ADR 49: Over the pace line, the lead works when the developer has nothing” (adr-49).
> - On its key point 3 (The 70% mark still stops lead tickets): no, it does not stop lead tickets. this should be the same logic as the pacing. developers go first, but if no developer and no reviews and no planning, do a lead ticket instead of being idle. i'm aware this may bring the capacity sooner in the week, but i'm keep no shut down my computer if all is done. the weekly pacing and 70% marks keep their value, but just in terms of prioritisation, not to pause the whole factory. i wonder if the last 10% rule is still useful in that new ruleset

## The lead, 2026-11-18 07:59

> I rewrote ADR 49 so the pace line and the 70% mark only decide the order: lead tickets go last but never stop, and only Claude's real limit stops them. I also answered your question about the last 10% rule. The ticket check passes except "accept ADR 49 first", which goes away once you accept it.
>
> 1. **The pace line and the 70% mark set the order, and no longer stop lead tickets**: Done as you said. Under the pace line, the board's order holds as today. Over the pace line, or past the mark, the order is: queued jobs first (planning, reviews, directions), then developer tickets, then a lead ticket instead of standing idle. Only Claude's real limit stops lead work: 100% of the week, or a pause after Claude refuses a job.
>    Action: ADR 49 items 2 and 3, and f264-01.
> 2. **The risk you take on: no planning at the end of the week**: The 30% reserve was the only thing that kept planning replies going when the week was nearly used up. Planning keeps its place first in the line, but not its tokens. In a week like this one the lead could reach 100% around Friday. After that, the planning room can't answer until Monday 16:00, and the fast lane can't help either. I'd still go ahead: lead tickets are cheap ($57 last week, against $284 for planning), and you said you'll switch off when everything is done.
>    Action: ADR 49 Consequences records it as your choice.
> 3. **Is the last 10% rule still useful? Yes, but only to set the order**: There's nothing left for it to open, because lead tickets no longer stop at the mark. It's still useful for the order, though. In the week's last hours, tokens left at the reset are lost, while the local developer costs nothing at any time. So in that stretch the lead shouldn't wait behind the developer: both go by the board's order. It costs no new code, because the existing rule already does exactly that. The 'use reserve' switch under the Claude week bar does the same for its 24 hours. The other choice is to drop the rule, so developers go first until the reset; you could lose some of the week.
>    Action: ADR 49 items 4 and 5. Tell me if you'd rather drop it.
> 4. **The 5-hour window stays as it is**: Your rule is about the week, so I kept the 5-hour window's 25% for you. At 75% a lead ticket parks for 5 hours at most, so when you plan, your replies come quickly. Applying the same 'order only' logic there would mean you sometimes wait for a planning reply while the lead uses that window.
>    Action: ADR 49 item 6. Tell me if you want it changed too.
> 5. **Simpler to build than my first draft**: 'Only the real limit stops it' is a question the runner already knows how to ask: the week treated as a cap at 100%. So `runner/allowance.py` doesn't change, and f264-01 now touches only how the next ticket is chosen, the dry run and the idle line. f264-02 changes the words on the Overview's 'Over pace' plate to 'developers first; the lead takes over when nothing else can run'. Only the wording of an existing plate changes, so there's no mock-up.
>    Action: Tickets f264-01 (lead) and f264-02 (developer) are rewritten.
> 6. **F250, Tell the phone when the factory is done for the week**: This fits what you said about switching off. After f264-01, the 'done' notification comes only when Claude's week is truly used up and nothing else can run.
>    Action: Nothing: F250 reads the idle line, which f264-01 changes.
> 7. **Getting the line moving**: f264-01 is itself a lead ticket, so the pace holds it until Thu 01:36 like the others. After you accept ADR 49 and approve the plan, put F264 in the fast lane so it goes first. Until then, the 'use reserve' switch under the Claude week bar on the Overview lets lead tickets run for 24 hours.
>    Action: You: accept ADR 49, approve the plan, put F264 in the fast lane.
>
> Proposals:
> - ADR 49: Claude's week pace and mark set the order, never stop the line (adr)
> - F264: the lead fills the gap (plan)

## The owner, 2026-11-18 08:05

> On point 4: This breaks the never idle rule, apply it there too. i can still plan, i'll just wait for the answers in the next window

## The lead, 2026-11-18 08:07

> I applied the same rule to the 5-hour window: past its 75% mark, lead tickets go last, and nothing parks there any more. I added a lead ticket, f264-03, for it. Two tickets fail the ticket check only because they rely on ADR 49, which is still Proposed; that goes away once you accept it.
>
> 1. **The 5-hour window works the same way now**: Done as you asked. Past the 5-hour window's 75% mark, the order is planning and reviews, then developer tickets, then a lead ticket instead of standing idle. Nothing parks at the mark any more. Lead tickets no longer park there, reviews, directions, escalations and checkpoints no longer wait there, and the desk item 'waits for Claude's 5-hour window, kept for you' goes. Only 100% of a window, or a pause after Claude refuses a job, stops Claude's work. A job cut off by the real limit still picks up again after the reset.
>    Action: ADR 49 items 2–4. The new lead ticket f264-03 removes the park, and f264-01 covers the 5-hour window in how the next ticket is chosen.
> 2. **What you'll notice**: On a busy evening, the lead can use the whole 5-hour window. A message you send then is answered when the window resets, up to 5 hours later, as you said you'd accept. Planning still goes first in the line, so the lead uses the window only when nothing of yours is waiting.
>    Action: Nothing: recorded as your choice in ADR 49.
> 3. **The 'use reserve' switches keep a meaning: the board's order**: With no reserve left to open, I kept both switches under the Claude bars and renamed them 'keep board order'. For their 24 hours, lead tickets keep the board's order past the mark instead of going after developers. That's useful when you want the lead to finish something first. The other choice is to remove both switches, which takes a control off the Overview and would need a mock-up.
>    Action: ADR 49 item 6. Tell me if you'd rather remove the switches.
> 4. **The Overview's words, no mock-up**: f264-02 now covers all the allowance words. The 'Over pace' plate says 'developers first; the lead takes over when nothing else can run'. Both marks say 'lead tickets go last from here', where the 5-hour one said 'kept for you from here'. The switches read 'keep board order', and the legend is rewritten to match. Nothing is added, moved or removed, so there's no mock-up.
>    Action: Ticket f264-02 (developer), after f264-01 and f264-03.
>
> Proposals:
> - ADR 49: Claude's pace and marks set the order, never stop the line (adr)
> - F264: the lead fills the gap (plan)
