# F94: While you were away: who, when and how long, said once

The planning thread behind F94's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-10 07:51

> Opus
> f9-25-seeds-and-planting
> The field's first two stations show real things: Planting counts the cards being planned with the owner, and tapping the seeds opens the sheet with the set-aside tickets listed, each a link. Opus · finished after 3 developer attempts
>
> i like the new what happened better but:
> - if the summary is short, it all shows as one line on desktop
> - it says twice who did it, at the beginning and at the end. the beginning is nicer to read, but the endhas slightly more informatio. remove duplicate and bring useful information at the top. it's missing at what time it finished and how long it took overall

## The lead, 2026-10-10 07:54

> Drafted on `plan/f94`: a Today/Proposed mock-up, the card's plan and one developer ticket. I couldn't run the pre-flight dry run from this job, so the ticket is checked by reading only.
>
> 1. **Why a short title runs into one line**: The name, the ticket, the title and the closing words all sit in one row that only wraps when it runs out of room. A long title drops below; a short one stays on the first line with everything else. I propose every row is always two lines, on a phone and a wide screen: the facts first, then the title alone.
>    Action: Ticket f94-01-away-row-facts (decision D4); see the mock-up's Proposed side.
> 2. **The name said twice**: The row starts with the agent's name, and the words at the end start with the same name again ("Opus · finished after 3 developer attempts"). The name stays at the start only. What the end added ("finished after 3 developer attempts", "lead ticket", "1st try", "2 attempts") moves up to the first line, right after the ticket.
>    Action: Same ticket (decision D1).
> 3. **When it finished**: The page already works out each ticket's finish (the end of its last job, which orders the list) but doesn't show it. It becomes "finished 10:32" on the first line, in local time. When the ticket finished on another day (a long stretch chosen on the replay bar), the day shows too: "finished 9 Oct 23:05".
>    Action: Same ticket (decision D2).
> 4. **How long it took: a choice**: I recommend the time from the ticket's first job starting to its finish, waits included: "took 2.6 h". That is what "overall" says, and it shows a ticket that sat half a night waiting for Claude. The cost: a ticket with 40 minutes of work and a 6-hour wait reads "took 6.7 h", which can look like slow work. The alternative is working time only (the jobs added up), which hides the waits. Showing both would crowd the line, so I left it out.
>    Action: Ticket as drafted uses first job to finish. Say "working time" if you prefer that, and I change D3 and the ticket.
> 5. **Mock-up to check before approving**: One page with a Today / Proposed switch, wide screen and phone, with what is new marked in dashed green. Only the f9-25 row is your real one; the other two rows and all times and durations are examples, since this job can't read the metrics database.
>    Action: Open docs/milestones/f94-mockup/away-rows.html, then approve the plan or tell me what to change.
> 6. **Who builds it**: One developer ticket, difficulty 3: small, unprotected, and it follows the code of the ticket that built these rows (f9-15). It also changes the three tests that expect the name inside the closing words. I could not run the pre-flight dry run here; the ticket's paths and names were checked by reading the code.
>    Action: Nothing: the runner's pre-flight checks it when the plan is approved.
> 7. **The card's title**: The card was named from the first words of your note ("Opus f9-25-seeds-and-planting The field's first two…"), which says nothing on the board. I renamed its heading to "While you were away: who, when and how long, said once". The file name and the key f94 are unchanged.
>    Action: Nothing.
>
> Proposals:
> - The rows of While you were away, Today and Proposed (mockup)
> - F94: While you were away: who, when and how long, said once (plan)
