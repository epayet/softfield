# F296: Show each milestone's net code lines on its card in the…

The planning thread behind F296's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-25 07:18

> Show each milestone's net code lines on its card in the board and on the milestone page beside its cost, so I can see which milestones grew the code without opening the review. From F286's review.

## The lead, 2026-11-25 08:24

> I've drafted the plan for F296: a mock-up, the card's Decisions and four tickets. All four pass the ticket check. I suggest one change to how the numbers are kept (point 1).
>
> 1. **Keep two numbers per ticket instead of asking git each time**: The dashboard can't run git, and the board redraws every 10 seconds. Counting from git each time would mean one git call per merged ticket on every refresh, more than a thousand calls today. F286's review already noted the same cost in the report. So the runner keeps two numbers on each ticket when it merges it: code lines added and code lines removed. Older tickets get theirs once, at the next run's start. The report then reads those numbers too, and its git calls go. This changes F286's rule that nothing is stored (ADR 52 item 4 says "computed from git each time"). The lead's ticket adds one line to the ADR saying so.
>    Action: Ticket f296-01 (lead): the two columns, filling them, the report reading them, the ADR line.
> 2. **On the board: a small "Code" plate**: A harvested card shows "Code +79 lines" (F286, Reviews look for complexity and leave the code simpler). A planted card that already has merged tickets shows its net "so far": F290, Split runner/loop.py into one module per job kind, reads +447 so far. A card with nothing merged, and a bug card, show nothing. A calmer version, just words on the count line, is beside it in the mock-up in case the plate is too much.
>    Action: Ticket f296-04 (developer).
> 3. **On the milestone page: right after the cost, readable while folded**: The closed "What it cost" fold now reads "$5.12, of which the review $1.35 · code +79 lines". Inside the fold, a "Code lines" row gives "+92 −13, net +79" with a small to-scale bar of added against removed.
>    Action: Ticket f296-02 (developer), which also adds the one shared reader the other pages use.
> 4. **Also a column on the Milestones page**: You didn't ask for this one. I'm adding it because the board shows only the latest four harvested cards, and the Milestones table is where you can compare every milestone side by side, beside "Claude $". It's a one-point ticket that reads the same numbers. Say no and I'll drop it.
>    Action: Ticket f296-03 (developer).
> 5. **No colour for good or bad, and net only on the board**: Growing isn't a fault, and shrinking isn't always good: F290's split adds 447 lines just to move code into new files. So the numbers stay in plain ink, with a − sign when the code shrank. The board shows only the net. Added and removed appear only inside the milestone page's fold, because a big rewrite with a small net looks quiet on the net alone (F290: +6,170 −5,723).
>    Action: Nothing: it's in Decision D4.
>
> Proposals:
> - F296: net code lines on board cards, milestone pages and the Milestones table (plan)
> - F296 mock-up: each milestone's code lines, on the board, its page and the Milestones table (mockup)
