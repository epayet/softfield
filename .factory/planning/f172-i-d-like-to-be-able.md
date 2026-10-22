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
>    Action: .factory/cards/f172-mockup/card-reserve.html; ticket f172-03 builds it.
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
>    Action: .factory/cards/f172-mockup/card-reserve.html; ticket f172-03 follows it.
> 5. **Ready for your approval**: All three tickets pass pre-flight except that they rely on ADR 34. Accept it, then approve the plan, both on this page.
>    Action: Accept ADR 34, then approve the plan.
>
> Proposals:
> - ADR 34: A card may use Claude's reserve (adr)
> - Mock-up: the card's reserve lever, the board's plate, the Overview's list (mockup)
> - F172: a card may use Claude's reserve (plan)
