# F124: Pause one project from the Projects page

The planning thread behind F124's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 04:23

> The plan for F124 is drafted on plan/f124: a mock-up of the Projects page, the card's Decisions and three tickets, all passing pre-flight. One change from the card's notes: the pause holds only the project's tickets, so its planning keeps answering and Resume can reach it.
>
> 1. **Using the existing project pause would cut the project off completely**: Today the runner drops any project that has a pause in the database and closes its session. Nothing of that project runs then: not its planning room, not its approvals, and not its requests. A Resume pressed on the dashboard would wait for ever, because that project's requests are only read at its own pick. So a project paused by you keeps its session and holds only its tickets, checkpoints and reviews, exactly what the whole-factory pause holds today. Its planning still answers you and Approve still goes through. "Being set up" keeps working as it does now.
>    Action: D1 and D2 in the card doc; ticket f124-01
> 2. **The top bar's Pause stays the whole factory's**: ADR 30 already gives each project its own pause and keeps the factory-wide pause for the machine, so this needs no new ADR. The two add up: either one holds a project's tickets. A paused project's line reads "Idle: paused by you since HH:MM", so the top bar never says the whole factory is paused when only one project is.
>    Action: D1 and D4
> 3. **Mock-up: a Pause / Resume on each project**: Today and Proposed of the Projects page, with the real projects and counts of tonight. softfield is shown running with Pause. travel-companion is shown just pressed: "Pausing…", dashed orange, can't be pressed again, with "On its way". coucou is shown paused, with a hazard-yellow edge, "Paused by you since 21:40. Its tickets wait; its planning still answers you." and Resume. On a wide screen the two sit side by side.
>    Action: .softfield/cards/f124-mockup/projects.html; ticket f124-02 builds it
> 4. **Three tickets, one of them a stretch**: 01 is mine (the runner and the dashboard's one write path are protected): the two new requests, the hold, and what the console and the dry run say. 02 is a developer's: the Projects page, after 01. 03 is a developer's stretch: once F132, One view of the whole factory, has built its Next in line, a paused project gets one line there, "Paused by you since HH:MM", instead of its tickets showing as next.
>    Action: f124-01, f124-02, f124-03 in .softfield/tasks/later/, queued at your Approve
>
> Proposals:
> - F124: pause one project from the Projects page (plan)

## The owner, 2026-10-27 08:07

> On point 3: what mockup. i don't see it. again.

## The lead, 2026-10-27 18:55

> The mock-up was drawn and is on plan/f124, but my last reply listed only the plan, so the page had nothing to open. It is listed below as its own proposal, beside the unchanged plan.
>
> 1. **The mock-up was drawn but never listed: my mistake**: The file `.softfield/cards/f124-mockup/projects.html` has been on plan/f124 since my last reply. A proposal's page shows a picture only when the proposal points at the mock-up file. I listed only the plan, which points at the card doc, so there was nothing to open. It is listed now as its own proposal, "Mock-up: pause one project on the Projects page". Open it and you get Today and Proposed side by side on a wide screen, or a switch on a phone. It hasn't changed since last time, so the tickets haven't either.
>    Action: The mock-up is listed below; the plan is listed again, unchanged
> 2. **Why it keeps happening, and the fix already waiting**: This is the "drawn, never listed" case that F165, A point that speaks of a mock-up opens it in one tap, found on 2026-10-21. The fix is already a ticket: f152-02-every-mockup-is-listed, in F152, A done card says where its review is. After each of my replies, the runner will list any mock-up I drew but didn't name. It hasn't run yet: it is 25th in the queue, behind F132 and others, so the slip can happen again until it lands. I recommend dragging F152 up the board, just under F142, Phone notifications, and sending the new order. It is one lead ticket of about 32 minutes.
>    Action: Drag F152 up the board and send the order (your move). Until f152-02 merges, I list every mock-up as its own proposal
>
> Proposals:
> - Mock-up: pause one project on the Projects page (mockup)
> - F124: pause one project from the Projects page (plan)
