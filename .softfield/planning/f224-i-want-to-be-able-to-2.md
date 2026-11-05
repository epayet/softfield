# F224: Approve a plan to go first in line, in the fast lane

The planning thread behind F224's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 09:38

> I want to be able to approve a plan in high priority option. When approved this way, rather than going at the end of the queue (to go after the other thread that is refactoring the queue system) it will for first rather than last with fast lane on directly

## The lead, 2026-11-05 11:13

> I've drafted the plan and a mock-up: an Approve first option on the review page, built after the queue work in F222.
>
> 1. **Approve first: one press instead of three**: Today this takes three steps: Approve plan, the Fast lane lever on the card's page, then a drag and Send. The review page gets an Approve first option that does all three in the approval's one commit. The card becomes #1 on the board with its fast lane on. If you press it on two cards, the later press stands first. Approve plan stays as it is.
>    Action: Tickets f224-01 (runner) and f224-02 (pages).
> 2. **The hidden cost: the fast lane passes everything and can spend the reserve**: A fast lane card goes ahead of planning and reviews and may use Claude's reserve. Its mark stays until sign-off, and the tickets it waits for come along. So one quick press on a big plan could spend a lot of the reserve while your planning replies wait. That's why I made it a fold, like Reject…, rather than a second button beside Approve plan: it takes two taps and says the cost in words. On a phone the dock stays one row. The lever and a drag undo it, except for what has already run.
>    Action: Open the mock-up. If you'd rather have one tap, say so and I'll draw a plain button.
> 3. **How I read your brackets: this is built after the queue refactor**: I took it that F224 is built after F222, A newly approved plan goes last on the board. It writes the same order list that F222's ticket f222-01 creates, so waiting avoids building it on the priority numbers and redoing it. If you meant the opposite, that this must not wait for F222, it can be built now on the numbers. That would need a follow-up ticket when F222 lands, so I don't recommend it.
>    Action: f224-01 depends on f222-01. Tell me only if you meant the other reading.
> 4. **Until it's built, F222 and this card won't get here on their own**: F222's plan and ADR 45 are still waiting for you. If you approve this plan first, its tickets simply wait for F222's, and nothing breaks. Both cards land far back behind about 117 ready tickets, and Approve first can't help because it doesn't exist yet. To have it soon: on F222's review page accept ADR 45 and approve the plan, approve this plan, then pull this card's Fast lane lever. The lane brings along what it waits for: f222-02, f222-01 and f196-02 from F196, A planted card with no tickets. Those are lead tickets, and they may use the reserve.
>    Action: Your choice when you approve; nothing to answer here. Both tickets on this card should cost about $2 of Claude by my estimate: lead tickets average $1.37, and f224-02 goes to a developer first.
> 5. **The edge cases I decided**: On a replan, Approve first moves a card already in line to #1 and turns its lane on, because that's what pressing it asks for. A plan with no ticket left to run is approved as a plain one, and the result says nothing went first. ADRs, merges and seeds don't get the option. If a plan waits for its ADR, the option is disabled, as Approve plan is. A refused approval changes nothing. No ADR is needed: it's only your existing lever and drag in one press, and the card records it as the one exception to ADR 45's 'what enters the line goes to the end'.
>    Action: Written as D2–D4 on the card and in f224-01.
> 6. **It shows as soon as you press it**: The review page goes on its way, as it does now. The card shows a dashed 'goes first · fast lane · on its way' plate in whichever stage it stands, and the Overview's Fast lane line names it. The card only moves to #1 at the runner's next pick. At sign-off, the review's picture of this card's own review page will show a settled proposal without the fold, so the fold itself gets checked by f224-02's browser test and by you, using the How to test steps on the card.
>    Action: Ticket f224-02 builds it from the mock-up.
>
> Proposals:
> - Approve first: first on the board, fast lane on (plan)
> - Approve first on the review page and the board (mockup)
