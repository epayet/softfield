# F233: The board's developer's view counts tickets that wait for the lead's direction

The planning thread behind F233's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-06 19:26

> Why is the factory not doing anything right now but on the board developer view it says there are cards that could be run by devs

## The lead, 2026-11-09 16:15

> The factory stopped because Claude's weekly allowance ran out. The board's developer's view was wrong to show work for the developers. I've drafted one ticket to fix what the board counts, and suggest a fast-lane move for the cause.
>
> 1. **Why the factory sat still from 6 to 9 November**: Claude's weekly allowance was used up on 5 November and only reset today at 16:00. The last developer job ended at 19:05 on 6 November. After that the runner had nothing it was allowed to start, because every developer ticket needed Claude first. Eight of them had failed twice, and the rule is that the lead then writes a direction before anyone tries again: f86-01, f228-01, f228-02, f89-03, f198-01, f207-02, f209-01 and f225-01. All the other developer tickets depend on a lead ticket that isn't done yet, such as f132-02, f164-03 and f9-29. So the runner was right to wait. It just didn't tell you why. F234 (the top bar says it's picking the next ticket while it does nothing) is about that missing message, on its own thread.
>    Action: Nothing for the runner itself.
> 2. **The board's developer's view was wrong**: It never checks whether a ticket is waiting for the lead's direction. Such a ticket still looks ready, so the view counted it as work the developers could start. Today it says 'Developers can work on 7 cards, 10 tickets, about 5 h 48 min' when the real number is 0. The fix: a ticket waiting for a direction counts as the lead's work. Its card reads 'developers tried f228-01 · waits for the lead's direction' and is no longer lit. Any developer ticket that depends on it is shown as waiting for it too. This is a small change that follows the existing escalated-ticket case, so a developer can build it. No mock-up: the look and the label already exist from F206, The board's developer's view counts tickets a developer has started. Only which tickets count, and a few words of the label, change.
>    Action: Ticket f233-01-direction-is-the-leads (developer).
> 3. **Where Claude's week went, and what to do about it**: From 2 to 5 November Claude jobs cost about $308 API-equivalent. $223 of that was 69 planner replies. Reviews took $44 and lead tickets only $14. You chose in ADR 44 to let planning skip the pacing, and ADR 44 warned that the week would run out early. It did, and the whole line stopped for three and a half days. The same thing is starting again: today 6 planner replies in 13 minutes took the 5-hour window from 14% to 71%. At 75% lead tickets park until that window resets. I'm not proposing to change the rule. I recommend putting F177, Planner replies: record their real cost, start cold threads fresh, in the fast lane, because it goes after what this week cost. If it doesn't bring planning down enough, we can talk about pacing planner replies, apart from your newest message on each card.
>    Action: Your choice: press the fast-lane lever on F177's card.
>
> Proposals:
> - The board counts tickets waiting for the lead's direction as the lead's (plan)
