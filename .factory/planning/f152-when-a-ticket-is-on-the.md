# F152: A done card says where its review is, and set aside says it won't run

The planning thread behind F152's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-20 07:40

> When a ticket is on the board growing and all tickets are done but it's still there. Does they mean it's waiting for a review round? If soit should state as much as it's not clear what's supposed to happen next. When it says 1 tickets has been set aside, do I need to do anything?

## The lead, 2026-10-20 07:45

> The plan and its mock-up are drafted on this branch. Approving it queues one developer ticket.
>
> 1. **Why a card stays in Growing with every ticket done**: Yes, it is waiting for its review. A card moves to Ripe only once every ticket is done and Claude's review has written its sign-off sheet. Until then it stays in Growing, and the board says nothing about why. Three cards are like that today. For F88, Add to lead memory that new factory features are themed, Claude finished the review at 07:40 this morning. The runner picks the sheet up at its next pick, right after this reply, and F88 moves to Ripe without you doing anything.
>    Action: Nothing for F88. Point 4 makes the card say this.
> 2. **F19 and F28: their reviews stopped, and F135 restarts them**: F19, Will I need to refresh the planning page, and F28, The pause button did nothing the first time: both reviews stopped on 15 Oct with 'end-to-end tests fail on staging'. No test failed. Softfield has had no end-to-end tests since the split, and the review still looks for them. F135, Reviews stop at once, fixes this: its ticket is ready and is about 7th in line, so a few hours away. Once it lands, both reviews run again on their own and the two Needs you items go. You don't need to do anything. If you want it sooner, drag F135 to the top of Planted on the board and press Send new order.
>    Action: Nothing; F135's ticket is already queued.
> 3. **'1 set aside': nothing for you to do**: A set-aside ticket never runs, and it doesn't stop its card from ripening. On F5, Steer from the phone, and the board, it is f5-10 (the Yes/No buttons for the 5-hour window). The reserve switch replaced it, and it is kept for the record. F9, Line polish, has five like it. The card's page lists each one as 'set aside'.
>    Action: The ticket in point 4 makes it read '1 set aside, won't run'.
> 4. **A done card says which step its review is at**: Once every ticket is done, the card gets one more line under its count, and so does the Stage line on its page. It reads 'Review next' (Claude reviews it before the next ticket, then it's yours to sign off), 'Review running' (who is reviewing it now), or 'Review stopped' (the runner's reason, shown under Needs you). The mock-up shows Today and Proposed on today's cards: F5, F19, F28 and F88.
>    Action: Mock-up .factory/cards/f152-mockup/review-note.html and developer ticket f152-01-review-step-on-the-card.
> 5. **No new 'Reviewing' stage**: I'd rather not add a seventh column between Growing and Ripe. Most of the time it would hold nothing, or one card for about 20 minutes. It would also be one more column to swipe through on a phone. Moving these cards to Ripe instead would break what Ripe means: 'needs your sign-off', shown only when something needs you. A line on the card says the same thing for less.
>    Action: Nothing, unless you'd prefer a stage of its own.
>
> Proposals:
> - F152: a done card says where its review is (plan)

## The owner, 2026-10-20 09:10

> On point 4: this makes it sound like you've done a mockup but i don't see it

## The lead, 2026-10-20 09:12

> The mock-up was drawn, but I listed only the plan, and the dashboard shows a mock-up only through a mock-up proposal. It is listed below now, with a ticket so this can't happen again.
>
> 1. **The mock-up was there but hidden: my mistake**: I drew it (.factory/cards/f152-mockup/review-note.html, on this card's branch). But I listed only the plan, and its link points at the card's doc. The dashboard shows a mock-up only from a proposal of its own that points at the file. So you got key points about a picture you couldn't open. It is listed below now as 'F152 mock-up: a growing card says what its review is doing'. Open it to see Today and Proposed for F5, F19, F28 and F88 on the Growing column, plus F19's page header.
>    Action: Mock-up proposal f152-mockup, listed below.
> 2. **So it can't happen again**: This shouldn't depend on me remembering. A lead ticket makes the runner check every planner reply: if the job drew or changed a mock-up that the reply didn't list, the runner adds a mock-up proposal for it ('Listed by the runner'). Then you can always open it.
>    Action: Lead ticket f152-02-every-mockup-is-listed, added to the plan.
>
> Proposals:
> - F152 mock-up: a growing card says what its review is doing (mockup)
> - F152: a done card says where its review is (plan)
