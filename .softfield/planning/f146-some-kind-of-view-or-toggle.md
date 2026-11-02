# F146: The board's Developers only view: what runs without the lead, and for how long

The planning thread behind F146's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> I want to see the board from a developer perspective. See what work can be done when only Devs are available

## The lead, 2026-10-27 09:24

> I've drafted a "Developers only" view for the board: a mock-up, the plan in F146's card doc and two tickets, all on `plan/f146`. Both tickets pass the ticket check. The counts below come from today's queue, sorted using the runner's own rule for which tickets are the lead's.
>
> 1. **What the developers can do alone today**: Only 10 of the 73 ready tickets can run without the lead: f59-01, f69-06, f81-01 to f81-06, f82-01 and f84-01. At the usual 32 minutes a ticket that is about 5 h 20 min of work, and then the line stops. The other 15 developer tickets are each waiting for a lead ticket. Seven tickets have no 'agent: lead' line but still count as the lead's, because they change protected files (f142-05, for one, changes runner/). The view sorts tickets the same way the runner does.
>    Action: The view shows this live: F146's two tickets.
> 2. **One switch, not two**: Your note asked for 'developers only' and 'developers only with no Claude'. Both settings give the same list of tickets, because a developer ticket never needs Claude to start. The difference is what happens afterwards. With no Claude at all, a failed attempt waits for its direction, which happened for about 1 in 6 tickets lately (25 directions for 143 developer tickets since 13 Oct). Cards whose last tickets are developers' also wait for Claude's review: today that is F69 (Light/night button), F82 (Text boxes grow) and F84 (Coming says which). A second switch would show the same tickets again. I'd make 'With no Claude at all' a third section of the view instead.
>    Action: One Who switch (Everyone / Developers only) with a 'With no Claude at all' section, as the mock-up shows. Say if you still want two switches.
> 3. **One lead ticket holds most of the developers' work**: f132-02-overview-live-every-project, on F132 'One view of the whole factory', is holding back 6 developer tickets: five of F132's and F62's one. It waits for nothing and is already #5 on the board. Every other lead ticket holds back one developer ticket at most. The view lists the lead tickets by how much developer work each would free, so you can see which card to move up, or mark to use Claude's reserve (F172) when Claude is short.
>    Action: Nothing now; the view's 'Waits for the lead' section shows it.
> 4. **Only a third of the ready work is the developers'**: 25 of the 73 ready tickets are the developers', and only 10 of those can run without the lead. My own rule is to keep developer tickets runnable alongside the lead's, and I am not keeping to it: when Claude runs short, the factory has about 5 hours of work left. This is evidence for F167 'Is the split between local developers and the lead smart and cheap?', which is waiting for my answer.
>    Action: I'll use these numbers when I answer F167; once built, the view will show them to both of us.
> 5. **Where it goes, and what it leaves out**: It's a third filter group on the board, after the search box and the kinds, so search and the kinds keep working together with it. In Developers only, the board shows the Planted stage only, with the cards that have developer work (14 today). Each card gets a line saying how many tickets can start now, how many come after them, and how many wait for which lead ticket. The 34 cards with only lead tickets are hidden and counted once. Dragging is turned off in this view so it can't reorder a partial list: you order the board from Everyone.
>    Action: The plan's D5.
> 6. **The mock-up**: Today is copied from board.html and its CSS. Proposed adds the Who switch, a striped 'Developers alone' panel above the field and each card's line, all with today's real tickets. The row of crates shows the order the developers would take them: solid for 'can start now', dashed for 'after another developer ticket'. Blue and orange are the factory floor's developer and lead colours, with a legend; the stripes and corner marks are decoration only.
>    Action: Read .softfield/cards/f146-mockup/developers-only.html.
> 7. **Who builds what**: f146-01 goes to the lead. It reuses the runner's own rules (who counts as the lead, the pick order, minutes per ticket), and getting them wrong would make the view disagree with what the runner actually does. f146-02 goes to a developer: a parameter, a template section and CSS, copying the kinds filter. In Developers only, f146-02 would itself appear under 'waits for the lead'.
>    Action: Two tickets, 02 waits for 01. They have no priority: the card's place on the board decides.
>
> Proposals:
> - F146: the board's Developers only view (plan)
> - F146 mock-up: the board, developers only (mockup)

## The owner, 2026-10-28 00:25

> I sent back your proposal “F146 mock-up: the board, developers only” (f146-mockup).
> - On its key point 1 (Who switch): I rather imagined a toggle that would display the board from the perspective of a developer. It would hide any milestone that is just lead work or depends on a lead doing some work first or a checkpoint. Rather than completely hiding it could highlight milestones it can work on somehow compared to others. I might want to re prioritise some tickets based on that view so that needs to work there. I thought something like that rather than a section at the top

## The lead, 2026-10-28 00:30

> I've redrawn the mock-up as you described it and updated the plan and both tickets to match. The tickets pass the ticket check.
>
> 1. **The same board, seen by a developer**: The view is now a lever after the kinds, and the separate section at the top is gone. Turned on, it shows the whole board, every card in its place, with three looks. Lit: developers can work on it now, like F81 'Bring the factory theme to the older pages' (1 ticket now, 5 after it). Half-dark: it has developer work that waits for a lead ticket, which it names, like F132 'One view of the whole factory' (5 tickets wait for f132-02). Faded: lead only, like F171 'Each card once on the board'. Each card also says its state in words, so the meaning doesn't rest on the colour alone. The other columns (seeds, sprouting, ripe, harvested) fade whole, because none of their cards has a ticket to run. Today the lever would light 4 cards: F59 'A weekly report page', F81, F82 'Text boxes grow' and F84 'Coming says which reply'. That is 9 tickets, about 5 h. 9 cards would be half-dark.
>    Action: Mock-up redrawn; f146-02 now builds this.
> 2. **Reordering works in this view**: Grips, ⋯ and 'Send new order' stay exactly as on the normal board, and the cards keep their places. A move you make here sends the same reorder as from the normal view.
>    Action: In the plan (D4, D5) and f146-02's Done when.
> 3. **What's worth reordering here**: The board has one order, and it's the runner's for everything. If you drag F81 from #39 to #4, it also runs ahead of lead work while Claude is available. That can be what you want, but you don't need it to keep developers busy: when Claude is short, the runner already skips lead tickets and takes developer ones in board order. What this view does well is show the half-dark cards: the lead ticket that frees the most developer work is worth lifting. That is f132-02, which frees 6 tickets, and F132 is already #3.
>    Action: Nothing to build; a way to read the view. Lifting a half-dark card's lead ticket is usually the move that pays.
> 4. **'Or a checkpoint'**: No ticket waits for a checkpoint today. A checkpoint reads finished work and can add fix tickets; it never holds a ready ticket back. Where Claude is still needed after the developers is the card's review. A lit card says so ('then Claude's review'), or names the lead ticket that comes next ('then the lead's f81-07'). That line also answers your 'no Claude at all' question on each card, so there's still one lever.
>    Action: In the plan (D4's `then`, D6).
> 5. **Tickets**: Same names, rewritten. f146-01-developer-line (lead) works out each card's look, its line and the totals, using the runner's rules, and leaves the board's order untouched. f146-02-developers-only-view (developer) adds the lever, the looks and the words, following the mock-up.
>    Action: Two tickets; 02 waits for 01.
>
> Proposals:
> - F146 mock-up: the board through a developer's eyes (mockup)
> - F146: the board's developer's view (plan)
