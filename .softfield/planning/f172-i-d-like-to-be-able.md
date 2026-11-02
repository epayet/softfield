# F172: Mark a card to use Claude's reserve, so only its tickets run past the mark

The planning thread behind F172's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-22 11:32

> I'd like to be able to use the reserve at the ticket level, so that high priority tickets get done even on reserve. i currently set the reserve on because there are some tickets i really want, but i'm keeping an eye on when to turn it off again once the tickets i want are on, so this would solve that problem for me and i won't have to keep an extra eye on it

## The lead, 2026-10-22 13:08

> I've drafted ADR 34, the card's plan (three tickets) and a mock-up. The only pre-flight problem is the expected one: the plan waits for ADR 34 to be accepted.
>
> 1. **A mark on the card, not on each ticket**: You think in cards, and a card is usually several tickets: F171, Each card once on the board, has four. If the mark sat on each ticket, you'd have to mark all four, and a ticket added by a later replan would be left out. So you mark the card once, from its page. All its lead tickets then run past the week's mark even with the switch off. Every other lead ticket still parks, as today. Developer tickets never needed the reserve: they run on the local model.
>    Action: ADR 34 items 1 and 3; tickets f172-01 and f172-02.
> 2. **Nothing to watch: the mark ends when the work does**: This is the part that solves your problem. The mark has no 24-hour timer. Once the card has no ready ticket left, it lets nothing else run, and the runner removes it when you sign the card off. You can turn the week's switch off now, mark the cards you want, and stop watching. The switch stays for 'everything, for 24 hours' when you want that.
>    Action: ADR 34 item 4.
> 3. **Also the tickets a marked card waits for**: Without this, a mark could do nothing. Marking F108, Desk boxes say when, would still leave it stuck behind F75's lead ticket parked at the reserve, because F108's ticket waits for it. So the mark also lets through the ready tickets its tickets wait for, all the way down, even when they belong to other cards. The cost: a mark can spend reserve on another card's ticket. It's always one the marked card needs, and the card's page will say so.
>    Action: ADR 34 item 3; f172-01.
> 4. **Why not 'top-priority cards use the reserve'**: That would need no lever, but I don't recommend it. Dragging a card up on the board would quietly start spending the reserve, and three cards share priority 1 today (F15, F26, F153). Spending the reserve should be a choice you can see, not a side effect of reordering.
>    Action: Recorded under the ADR's alternatives.
> 5. **Your choice: the week's reserve only, or your 5-hour share too?**: I recommend A: a mark lets tickets past the week's reserve only. Your 25% of the 5-hour window stays behind its own switch. A ticket held there goes on by itself within a few hours, when the window resets, so marking a card doesn't eat into the room you keep for your own sessions. B: a mark passes both, which is faster for the card, but a busy marked card could take your 5-hour share while you're working with me.
>    Action: Answer A or B here; A is in ADR 34 item 5.
> 6. **Risk: the reserve also keeps reviews and planning going**: The week's reserve (the 30% above the mark) is what checkpoints, reviews, escalations and your planning jobs run on. Mark many cards and the week can reach 100%. Claude then stops for everything until the reset, this planning room included. The switch has the same risk today. To keep it in view, the Overview lists the marked cards under Claude's week meter.
>    Action: In the ADR's consequences; ticket f172-03 shows the list.
> 7. **What you'll see: mock-up**: Three places change. On the card's page there's a 'may use Claude's reserve' lever under the title, styled like the Overview's switches. It shows only on a planted or growing card, and goes halfway with a dashed edge until the runner takes it. On the board, a striped 'uses Claude's reserve' plate sits on each marked card. On the Overview, a 'Past the mark for: F142, F171' line sits under the week meter. Today and Proposed use today's values: the week at 67%, its mark at 70%, both switches on until Fri 09:35.
>    Action: .softfield/cards/f172-mockup/card-reserve.html; ticket f172-03 builds it.
> 8. **Who builds what, and the order**: f172-01 (mine, runner): the runner reads the mark and lets those tickets through. f172-02 (mine, runner): the lever's request writes the mark into the card and frees its parked tickets at once. It reuses the existing 'reserve' request, so the dashboard's protected write doesn't change. f172-03 (developer): the lever, the board plate and the Overview line, following the allowance panel's switch. They run in that order, at priority 2, so they come soon after F142.
>    Action: Accept ADR 34 on this page, then approve the plan.
>
> Proposals:
> - ADR 34: A card may use Claude's reserve (adr)
> - Mock-up: the card's reserve lever, the board's plate, the Overview's list (mockup)
> - F172: a card may use Claude's reserve (plan)

## The owner, 2026-10-22 14:36

> On point 5: I want it to use both. The button essentially means, this is more important than anything else so use all reserve for it

## The lead, 2026-10-22 14:37

> I've changed the drafts so a marked card uses both reserves: the week's and your 25% of the 5-hour window. ADR 34, the three tickets and the mock-up all say so now. The only pre-flight problem is the expected one: the plan waits for ADR 34 to be accepted.
>
> 1. **Both reserves: done**: A marked card's lead tickets, and the ones they wait for, now use the week's reserve and your 25% of the 5-hour window, with both switches off. A ticket of the card already waiting at either reserve goes at the next pick, and its item leaves your desk. One thing still holds them: a real limit. When a window is at 100%, or Claude has refused and is resting, nothing can run until the reset.
>    Action: ADR 34 items 3, 5 and 8, with your answer under 'Settled with the owner'; tickets f172-01 and f172-02.
> 2. **Cost: your own sessions with Claude**: Your 25% of the 5-hour window is the room kept for you to work with Claude yourself, here or in a terminal. A busy marked card can now use it up, and then your own Claude session waits for the window's reset, at most five hours. That's the meaning you gave the button, so I've kept it. Turning the mark off gives the room back at the runner's next pick.
>    Action: In the ADR's consequences.
> 3. **The mark picks who may use the reserves, not who goes first**: 'More important than anything else' has two halves. At a reserve, marked tickets already go before every other lead ticket, because the others park. Below the marks, the board's order decides, as today. So for a card you want first everywhere, mark it and drag it to the top. I'd keep the two separate: if marking also moved the card to the top, turning the mark off would leave it there.
>    Action: Nothing.
> 4. **Mock-up updated**: The Overview now shows both of Claude's meters, with today's values: the 5-hour window at 91% (your mark at 75%) and the week at 67% (its mark at 70%). Under them, one line reads 'Past both marks for: F142, F171'. On the card's page, the lever's line says it uses both reserves. In Proposed, with both switches off, F142 (Phone notifications) and F171 (Each card once on the board) go on, and F153 (Sonnet does the easier lead tickets) waits for 12:40.
>    Action: .softfield/cards/f172-mockup/card-reserve.html; ticket f172-03 follows it.
> 5. **Ready for your approval**: All three tickets pass pre-flight except that they rely on ADR 34. Accept it, then approve the plan, both on this page.
>    Action: Accept ADR 34, then approve the plan.
>
> Proposals:
> - ADR 34: A card may use Claude's reserve (adr)
> - Mock-up: the card's reserve lever, the board's plate, the Overview's list (mockup)
> - F172: a card may use Claude's reserve (plan)

## The lead, 2026-10-22 15:15

> Approved by the owner on 2026-10-22: approved plan/f172: queued f172-01-marked-cards-pass-the-reserve, f172-02-reserve-request-marks-a-card, f172-03-reserve-lever-on-the-card

## The owner, 2026-10-23 19:38

> It works well but it should be accessible from the board rather than from the planning. Not the board itself but the milestone page I think, when I click on a ticket. Also I want tbag when the flag is on at ticket level, it takes priority even over planning and reviews

## The lead, 2026-10-26 22:55

> I moved the lever to the card's page you open from the board, and drafted ADR 35 so a marked card's tickets go before planning, reviews and everything else. ADR 35 must be accepted before the plan can be approved; that is the only thing pre-flight reports.
>
> 1. **The lever moves to the card's page under the board**: When you tap a card on the board, you land on its card page (/milestones/…). The lever becomes a 'Reserve' row in that page's header, under Stage, Priority, Area and Tickets, and it leaves the planning thread. The Overview's list of marked cards links to those pages too. I read 'when I click on a ticket' as tapping a card on the board. If you meant each ticket's own page, say so here: I'd still recommend the card, because a ticket added later by a replan would come unmarked.
>    Action: Ticket f172-05 (developer), ADR 35 item 4.
> 2. **A marked card goes before everything, planning and reviews included**: It's needed: this evening, Next in line had 41 planning jobs, a direction, a checkpoint and F68's review ahead of the first ticket. A marked card would have waited hours. Now its ready tickets, and the ones they wait for, go first, in the board's order. This changes the order we agreed last round, where the mark only decided who uses the reserve.
>    Action: ADR 35 item 1; ticket f172-04 (mine, runner).
> 3. **A fix for a marked ticket goes with it**: When a marked ticket fails, the lead's direction or escalation for it is part of that ticket's work. It goes first too. Otherwise the ticket would sit stopped behind the planning jobs, which is the wait you want gone.
>    Action: ADR 35 item 2; f172-04.
> 4. **Cost: your replies wait while a marked card runs**: This is the hidden cost. While a marked card has work, my replies in the planning room wait behind it, about 33 minutes per ticket, so hours for a card with several. Checkpoints and other cards' reviews wait too. Nothing merges unchecked: each ticket still passes its gates. The way out is already there: pausing from the top bar holds every ticket, marked ones too, and lets planning through. So when you want to talk, pause; when you resume, the card carries on.
>    Action: Written in ADR 35 item 3 and its consequences; nothing to build.
> 5. **Next in line shows it**: On the Overview, the marked card's tickets sit on top, in a striped bay reading 'Goes first: its card uses Claude's reserve', above the planning jobs and the review. That way you can see it working without opening the runner's log.
>    Action: Ticket f172-06 (developer), after f172-04.
> 6. **Mock-up**: It uses tonight's real values. The Proposed side shows F142's card page with the Reserve row, the planning thread without the lever, and Next in line with f142-05 moved above 41 planning jobs, a direction, a checkpoint and F68's review. The lever now reads 'goes first, uses Claude's reserve', so it says both things it does.
>    Action: .softfield/cards/f172-mockup/goes-first.html; tickets f172-05 and f172-06 follow it.
> 7. **Order and approval**: f172-05 (the lever's move) can start as soon as you approve. f172-04 and f172-06 wait for ADR 35. The tickets carry no priority: the card's place on the board decides, as you set on F173. Accept ADR 35 here, then approve the plan.
>    Action: Accept ADR 35, then approve the plan, both on this page.
>
> Proposals:
> - ADR 35: A card marked to use the reserve goes first (adr)
> - Mock-up: the lever on the card's page, and Next in line with a marked card first (mockup)
> - F172, second round: on the card's page, and first in line (plan)

## The owner, 2026-10-26 23:37

> Let's call it fast lane and it goes before everything. Design accordingly

## The lead, 2026-10-27 13:52

> The mark is now called the fast lane everywhere, and ADR 35 is redrafted so the fast lane goes before everything. The four tickets pass pre-flight except that 04 and 07 wait for ADR 35 to be accepted.
>
> 1. **It's called the fast lane, everywhere**: Every page and line that names it now says 'fast lane': the card page's lever (a 'Fast lane' row), the plate on the board, the line under Claude's meters on the Overview, the runner's commits ('F142 in the fast lane, by the owner') and the card's own header (**Fast lane:** yes). F142 and F173, which you've already marked, carry over in the same change, and the old wording still counts, so no mark is lost.
>    Action: New ticket f172-07 (mine, runner); f172-05 changes the pages' words.
> 2. **Before everything**: A fast-lane card's ready tickets, and the tickets they wait for, are the runner's next jobs. They go before planning, escalations, directions, checkpoints, reviews, a parked ticket due to try again, and every other card. A fix for one of them, the lead's direction or escalation, goes first with it, since it's that ticket's own work. With two cards in the lane, the higher one on the board goes first.
>    Action: ADR 35 items 2 and 3; ticket f172-04.
> 3. **Your pause still stops it, and so does a real limit**: I kept two exceptions to 'everything'. First, your pause: it is your one stop button, and pausing is how you get to talk to me while the lane runs (planning goes, the lane waits). If the lane ignored it, the only way to stop the factory would be to take each card out of the lane. Second, Claude running out: when a window is used up, no lane can run, so the line takes a developer ticket meanwhile rather than standing idle. If you want the lane to run through your pause as well, say so here.
>    Action: ADR 35 item 5; nothing unless you disagree.
> 4. **Cost: your replies wait, starting with this one**: Right now F173 and F142 are marked. Approve this and f173-02 and f142-05 run before the 15 planning jobs queued this morning, including your replies here. That's about an hour, at 32 minutes a ticket. A card with five lead tickets in the lane holds planning for close to three hours. When you want an answer sooner, pause.
>    Action: In ADR 35's consequences.
> 5. **The lane's order builds on F173**: F173 (The board's order is the order the work runs in) has a ticket, f173-02, that lets a waited-for ticket run in its waiter's place. The fast lane's order needs exactly that, and both change the same runner function. So f172-04 waits for f173-02, which is in the lane itself and next in line anyway.
>    Action: f172-04 depends on f173-02.
> 6. **Mock-up updated**: It uses this morning's values. On the card page, a 'Fast lane' row holds the lever, and the planning thread no longer has it. The board's plates read 'fast lane' on F173 and F142. Next in line opens with a striped 'Fast lane · goes before everything' bay holding f173-02 and f142-05, ahead of the 15 planning jobs, 2 escalations, 4 directions, the checkpoint and F68's review. Under Claude's meters the list reads 'Fast lane:'.
>    Action: .softfield/cards/f172-mockup/goes-first.html; f172-05 and f172-06 follow it.
> 7. **Order and approval**: The tickets run in this order: f172-07 (the name, mine), then f172-05 (the lever moves to the card page and the pages say 'fast lane', developer) and f172-04 (the order, mine, after f173-02), then f172-06 (Next in line, developer). Accept ADR 35 on this page, then approve the plan.
>    Action: Accept ADR 35, then approve the plan.
>
> Proposals:
> - ADR 35: The fast lane (adr)
> - Mock-up: the fast lane on the card page, the board and the Overview (mockup)
> - F172: the fast lane (plan)
