# F263: Show the lead's direction to a developer's last attempt on the Overview

The planning thread behind F263's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-17 23:02

> On the console run you can see the advice the lead gave a ticket when it got directed, I'd like to see that on the dashboard too in overview

## The lead, 2026-11-17 23:07

> I've drafted a plan: the lead's direction shows on the Overview, in Now while the attempt runs and folded in While you were away once the ticket has merged. The mock-up shows f216-05's real direction from tonight.
>
> 1. **What the console shows, and why the dashboard can't show it yet**: Before a developer's last attempt, Opus writes a direction: a few lines of advice, saved as a file in the ticket's logs. The console prints only its first line (the '↳ [claude-opus] …' under the direction's end line). The dashboard has nothing of it. The direction job's page shows that job's note, but that note says what went wrong, not what the lead told the developer to do. The file also gets overwritten by the next direction, and it can sit in an older run's folder, so the dashboard shouldn't read it from there.
>    Action: The runner keeps the whole text in the database on the direction job's row (f263-01, a lead ticket, since runner/ is protected).
> 2. **Show it in two places on the Overview, not only in Now**: You asked for the Overview, so I put it in two places. Now is the main one: during the last attempt, the direction sits on a plate under the ticket's title. But a last attempt takes about an hour, and you mostly look later from your phone, so a plate only in Now would usually be gone by the time you look. So the ticket's row in While you were away keeps it too, folded. Tonight there were three directions (f216-05, f133-03, f12-10).
>    Action: Two developer tickets: f263-02 for Now, f263-03 for the away rows. Strike f263-03 if Now alone is enough.
> 3. **On a phone it stays short, so the readouts stay above the fold**: A direction runs to five long lines: f216-05's first line alone is about 280 characters. In Now, the plate shows its first line cut to two lines, as on the console. A tap opens all of it, with a link to the direction's job and what it cost ($0.44 for f216-05). In the away rows it starts folded.
>    Action: Drawn in the mock-up; D3 in the card.
> 4. **An open direction holds the 5-second refresh**: The Now panel is redrawn every 5 s, which would snap an open plate shut while you read it. While a direction plate is open, the Overview holds its refresh, the same way it already does for a half-typed comment. Folding the plate lets the page catch up.
>    Action: Part of f263-02.
> 5. **Only directions given after the change show**: Tonight's three directions are only in files, and two of them could be overwritten. I'm not backfilling them: it would mean reading old run folders for little gain. The first plate will show at the next direction after f263-01 merges.
>    Action: Nothing to do; written in D1.
> 6. **When it runs**: Three tickets, about three hours of work: one lead ticket, then two developer tickets that each wait for the one before. The card goes in at its place on the board, behind the ready cards. Lead tickets are also waiting for Claude's week pace until about Wed 20:48. If you want it sooner, drag F263 up on the board.
>    Action: Nothing to do; your Approve queues it.
>
> Proposals:
> - F263: the lead's direction on the Overview (plan)
> - The direction in Now and in While you were away (mockup)
