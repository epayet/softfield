# F154: Each board stage says what it means and what moves a card on

The planning thread behind F154's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-20 07:40

> What's the difference between planted and growing? I forgot and on mobile it's not very clear

## The lead, 2026-10-20 07:54

> I've answered your question and drafted a small plan for clearer stage words: a mock-up of the board on a phone and one developer ticket, which passes the ticket check.
>
> 1. **Planted against Growing**: Planted means the plan is approved and its tickets are waiting in the queue, but none has started yet (F42, The space to scroll on a proposal card: 0 of 2). Growing means at least one ticket has started. The card stays Growing until every ticket is done and Claude's review is in; then it turns Ripe for your sign-off. For a bug, it's the same idea: ready means Planted, running or stopped means Growing.
>    Action: Nothing: this is how the board works today (`_milestone_stage` in factory_dashboard/board.py).
> 2. **Growing doesn't mean it's running right now**: The runner builds one ticket at a time. So of today's 13 growing cards, only the one with a "Now:" line is being worked on. The others are waiting their turn: F15, Reprioritising tickets, waits for F73, and F19, F28 and F88 have every ticket done and are waiting for their review. That is part of why the stage reads unclearly.
>    Action: Say it in the stage's own words (point 3). F152, A done card says where its review is, already covers the line for cards with every ticket done.
> 3. **Why it's unclear on a phone, and the fix**: Under 640 px the board hides its explanation paragraph, so only the stage head is left: "tickets ready" for Planted and "in the factory" for Growing, and both sound alike. I propose new words for each stage plus a second line, "Next: …", saying what moves a card on. For example: Planted "tickets ready, none started yet · Next: the runner starts its first ticket"; Growing "work started, one ticket at a time · Next: every ticket done, then Claude reviews it". It shows the same on every screen, and a card's page uses the new meaning too. I chose this over a pop-up key: you'd have to tap to open a pop-up, but the stage head is always in view, right under the plot you pressed.
>    Action: One developer ticket, f154-01-stage-says-what-next, built from the mock-up .factory/cards/f154-mockup/stage-words.html.
> 4. **Same files as F152**: F152, A done card says where its review is, has a draft that also touches board.html and dashboard.css, but on the cards rather than the stage heads. Both can be built in either order. It isn't a repeat: F152 explains a done card's review, and this card explains the stages.
>    Action: Nothing: they stay two cards.
>
> Proposals:
> - Each stage says what it means and what moves a card on (plan)
> - Board on a phone: Planted and Growing heads, today and proposed (mockup)

## The owner, 2026-10-20 09:10

> On point 1: having 2 columns makes it harder to reprioritise. if i just planted something higher priority than a currently growing piece, i can't prioritise it higher. let's make it 1 column instead, planted is fine. perhaps we could find a way to show that a planted piece is currently growing because it has some stuff in progress, but it should all be in the same column.

## The lead, 2026-10-20 11:14

> I've reworked the plan as you asked: Planted and Growing become one Planted column, and a card with work started gets a "growing" tag. The mock-up and the ticket are updated, and the ticket passes the ticket check.
>
> 1. **One Planted column: agreed, and it's simpler than it looks**: You're right. The runner already treats the board's order as one list of every open card, and the line you send from the board doesn't say which stage a card is in. Only the dashboard splits Planted from Growing and keeps each drag inside one column. That's why F151 (I had to restart the runner) can be #1 in Planted but never go before F106 (Where do blocked tickets go). The factory floor already counts both as one station. So the change is in the dashboard only: five stages (Seed, Sprouting, Planted, Ripe, Harvested), and one Planted column of today's 38 cards in the runner's order, where you can drag any card above any other.
>    Action: One lead ticket, f154-01-stage-says-what-next, built from the updated mock-up .factory/cards/f154-mockup/stage-words.html.
> 2. **How a planted card shows it's growing**: A card with a ticket started keeps the orange edge that growing cards have today. It also gets a small "growing" tag with the plant drawing, next to its number. The one being built right now still has its "Now:" line. The column's head says "in line for the factory, #1 first · 38, 12 growing", with "Next: every ticket done, then Claude reviews it" under it (the Next line you agreed last round). A card's page says "Planted · growing since" the day its first ticket started. I kept orange because it already means "work has started" on the board and the floor, so the tag is the only new thing to learn.
>    Action: In the mock-up's Proposed: F5, F15, F106 and F26 are tagged, and F151 and F142 are not.
> 3. **It waits for F152's review line**: F152 (A done card says where its review is) was approved, and its ticket is in the queue. It adds a "Review next / running / stopped" line to growing cards whose tickets are all done. Once the columns are merged, those cards are planted cards with work started. So this ticket waits for F152's and keeps that line on the same cards. If it went first, F152's ticket would aim at a stage that no longer exists.
>    Action: f154-01 now waits for f152-01-review-step-on-the-card.
> 4. **The lead builds this one, not a developer**: No protected file is touched, but the stage list is read by the board, a card's page, the factory floor, the board's script and many tests. A local developer would likely miss one of them, and Claude would end up finishing it. About one hour of lead work.
>    Action: The ticket is marked agent: lead.
>
> Proposals:
> - One Planted column, a growing tag, and stages that say what comes next (plan)
> - Board on a phone: two columns today, one Planted column proposed (mockup)
