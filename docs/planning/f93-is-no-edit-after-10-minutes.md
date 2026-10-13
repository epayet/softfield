# F93: Developer attempts get 20 minutes before the no-edit stop

The planning thread behind F93's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-13 13:48

> From F111, merged here:
> [07:58:52] ── f53-02-parked-review-crate · developer · d3 ──
> [07:58:52] A review that waits for Claude shows as waiting in the line's queue, behind the tickets that can run, instead of as number 1 with nothing said.
> [07:58:52] ▶ [claude-opus] direction
> [08:00:15] ■ [claude-opus] direction done · 1 min · $0.68
> [08:00:15]   ↳ [claude-opus] Both attempts stopped with no edit: you read `factory.js`, `conftest.py`, `overview.py` and the test files, and planned the whole change. You already understand it. Read nothing else; every fact you still need is below. Make the first edit within two minutes, in `factory_dashboard/line.py`, and run the tests after each step.
>
> i wonder if 10 minutes timeout is too aggressive

## The lead, 2026-10-13 13:55

> Yes, the logs say the 10-minute stop is too short; I drafted the card's decisions and one lead ticket to move it to 20.
>
> 1. **Yes, 10 minutes is too short**: Of the 29 developer attempts from 10 to 13 October, 16 were stopped by this rule, on 9 tickets. The 13 that did edit made their first edit after 1.6 to 9.2 minutes (6.3 in the middle), and four of them after 8 minutes or more. So the stop sits right where first edits still happen, and the ones that would have come at minute 11 or 12 are among the 16.
>    Action: Move the stop to 20 minutes (ticket f93-01, below).
> 2. **The attempt you pasted was working, not stuck**: The first attempt on f53-02 read files for 5 minutes, then was 5 minutes into one step when it was stopped; its thinking ends on "Now I need to implement this". The second was 6 minutes into a step. Each step sends the whole conversation again (67,000 tokens), so 10 minutes is only five or six steps. Even the third attempt, told to edit within two minutes, made its first edit at 5.6 minutes.
>    Action: Nothing more: the evidence is written on the card under "What we know".
> 3. **Why 20 and not 15, and what it costs**: The slowest first edit seen is 9.2 minutes and one step ran past 6, so 15 leaves less than one step of room. The rule was made to stop attempts that made no edit in 25 to 30 minutes, and 20 still stops those. The cost: an attempt going nowhere holds the GPU 10 minutes longer, 30 for a ticket that loses all three. An attempt saved avoids a wasted 10 minutes and often a direction ($0.68 here) and an escalation where Opus builds the ticket.
>    Action: 20 minutes in the ticket; say 15 if you prefer the cheaper cut.
> 4. **A longer stop won't fix tickets that are too big**: Two tickets (f3-08, f9-25) lost all three attempts to this stop, the directed one too. More minutes probably don't save those: they were past the local developer, and the fix is smaller tickets. If more than a quarter of attempts are still stopped at 20 minutes, the problem is planning, not the stop.
>    Action: The factory's periodic review (F59) reads the share from the session reports; 16 of 29 is the number to beat. No ticket.
> 5. **The direction stays after two stops**: The review of F53, "Why is milestone diff review waiting", suggested skipping the lead's direction after two no-edit stops and escalating at once. The logs disagree: the directed third attempts on f53-02 and f5-08 wrote the whole change. I'm not changing it.
>    Action: Nothing; looked at again once the 20-minute stop has run for a while.
> 6. **One lead ticket, at priority 1**: The change is a number and its words in `runner/local_model.py`, which is protected, so it is a lead ticket. It is a timeout, which the runner's settings say can be tuned freely, so no ADR. I gave it priority 1: every developer ticket that runs before it risks the same lost attempts.
>    Action: Approve the plan to queue f93-01.
>
> Proposals:
> - F93, Developer attempts get 20 minutes before the no-edit stop (plan)
