# F222: A newly approved plan goes last on the board

The planning thread behind F222's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 05:46

> When milestones plans get approved, do they get added to the back of the queue consistently? I sometimes struggle to find them again, it'll be easier if they get at the end and I can reshuffle manually if that's not the case atm

## The lead, 2026-11-05 05:49

> No, not consistently. This reply drafts one ticket that puts a newly approved card last on the board.
> `softfield check-tickets` passes the new ticket. It flags only two old F9, line polish tickets that are set aside, f9-06 and f9-12, and neither affects this plan.
>
> 1. **Approved plans don't reliably go last**: Approving a plan only changes the card's state. The card keeps the priority it had as an idea, usually 100, and the board sorts by priority, then card number. So a new card lands last only if it has the highest number among the 100s, and an older one lands in the middle. F209, The board lights the card at work, was approved after F215, A plain floor, and F216, A shorter review page, yet it stands before both (#49, against #50 and #51). Approving F133, Each project gets its own card letter, would put it about #38 of 52.
>    Action: Ticket f222-01 fixes this.
> 2. **The fix: last behind everything open**: When an approval first puts a card in line, its priority becomes one more than the highest of every other open card and bug. Nothing else is renumbered, so your existing order stays. A replan or a second plan on a card already in line keeps its place. A plan with no ticket doesn't enter the line, so it stays put too. The approval's result will say the card went last.
>    Action: One lead ticket, because the runner is protected. It goes after f196-02 from F196, A planted card with no tickets, which changes the same lines.
> 3. **A cost you should weigh: last is a long way back**: 103 tickets are ready at about 40 minutes each, nearly three days of steady work. An approved card will wait behind all of them until you move it, so anything urgent needs a drag or the fast lane. A place you dragged a card to before approving is also lost. I still recommend your rule, because one predictable spot beats exceptions: only three unplanned cards sit above 100 today, F11, test, F27, Planner tasks during a pause, and F43, Approving part of a proposal, all at 90.
>    Action: Nothing to do unless you want a dragged place kept. In that case, tell me and I'll change D3.
> 4. **Queued bugs have the same problem, and I left them out**: A set-aside bug you queue also lands at its old number. bug-29, Archive row shows it on its way, has priority 56, so it would land ahead of every card at 90 or 100. I kept this out because you asked about plans, and because a bug has no plan or approval step, so it would change the Queue and Try again paths too.
>    Action: My suggested fix is a second small ticket that sends a bug you queue to the back as well. Tell me if you want it; otherwise bugs stay as they are.
> 5. **No mock-up**: No page changes its look. The board shows the same cards and only the order differs, and the approval's result gains a few words.
>    Action: None, unless you want one.
>
> Proposals:
> - A newly approved plan goes last on the board (plan)

## The owner, 2026-11-05 08:13

> Retire the priority system so that only queue order matters, it will be simpler this way. Then ensure that new tickets get appended to the end of the queue after planning is approved so that I know where to find them to reorder

## The lead, 2026-11-05 08:25

> I've drafted the full retirement: ADR 45, a new plan of four lead tickets that replaces the last one, and a mock-up.
> The tickets pass pre-flight once ADR 45 is accepted, which it reports as the only thing outstanding on them.
>
> 1. **Agreed: the number goes, but the order still has to live somewhere**: Since F173, The board's order is the order the work runs in, the number only means a place, and it's badly stored: about 30 open cards share 100, so their order is really their card number. That tie is why F209, The board lights the card at work, stands ahead of cards approved before it. I propose one list per project, `.softfield/order.txt`, with one card or bug per line, which only the runner writes. A drag then changes one file instead of many.
>    Action: ADR 45 and ticket f222-02.
> 2. **This costs more than hiding the word, and I still recommend it**: It takes four lead tickets, about $10 by my estimate: recent lead tickets average $1.37, but these are bigger, and about 280 test lines name the field. Hiding the word and keeping the numbers would cost about half, but the ties and many-file drags would stay, and it wouldn't be what you asked for. This is also the second time you've asked (2026-10-22 and today).
>    Action: Nothing to do, unless you prefer the cheaper version.
> 3. **A newly approved card goes to the very end**: Approving a card's first plan moves it behind everything open, in the approval's own commit, whatever its number or earlier place. A replan, a second plan or a plan with no ticket leaves it where it is. The approval's result says it went last.
>    Action: Ticket f222-01, after f196-02 from F196, A planted card with no tickets, which changes the same lines.
> 4. **A change from my last reply: queued bugs go to the end too**: I had left bugs as they are unless you said otherwise. With the number gone, a set-aside bug needs a new rule anyway, and one rule is simpler: whatever enters the line goes to the end. Try again on a blocked ticket keeps its place, because that ticket never left the line.
>    Action: It's part of ticket f222-01. Tell me if you'd rather bugs kept their old place in the list.
> 5. **Your current order doesn't change**: The first time the runner finds no list in a project, it writes one in today's exact order, so coucou and travel-companion move over too. A test compares the order before and after. The main risk is a wrong order at that moment, and a card out of place is fixed with a drag. The numbers are removed last, once the runner and the pages read the list, so main stays correct after each ticket.
>    Action: Tickets f222-02 and f222-04.
> 6. **What the pages show instead**: Next in line says the ticket's card in place of "priority N". A card's page says "Place: #1 in Planted", the same number the board shows. The Priority column leaves Milestones and the Set aside table on Tickets. A set-aside ticket says it goes to the end of the line. The mock-up shows each of these on real cards.
>    Action: Open the mock-up. Ticket f222-03 builds it.
> 7. **One number stays: the Projects page's order**: Projects have their own order number, which you never see and which only sets the order of projects. F123, Projects page: drag projects into order, and F193, The project picker follows the owner's project order, both rely on it. It isn't part of the queue, so removing it would only add cost.
>    Action: None.
> 8. **Accept the ADR first, then approve the plan**: The plan changes a rule in an accepted ADR and the ticket format, so it needs ADR 45 accepted before it can be approved, and the approval is refused until then. Both buttons are on this page. Nothing on the line needs pausing, because no waiting ticket changes. F222 itself lands last among the cards at 100, so drag it up if you want this soon.
>    Action: Press Accept on ADR 45, then Approve on the plan.
>
> Proposals:
> - ADR 45: The queue's order is one list, and the priority number goes (adr)
> - Where the priority number leaves the pages (mockup)
> - One queue list, and approved plans go to the end (plan)

## The owner, 2026-11-05 09:38

> On point 1: Why a separate text file rather than using the main db. Why not store a rank or order number in each ticket instead. That way when I browse a card I could see it's number in the queue as well

## The lead, 2026-11-05 11:09

> You'll see the number while browsing, on a card's page and on a queued ticket's page, but I recommend working it out from the list rather than storing it. I've revised ADR 45, the mock-up and f222-03 to match.
> Pre-flight still reports only that ADR 45 must be accepted first, as before.
>
> 1. **Seeing the number while you browse: yes**: A card's page shows "Place: #1 in Planted", the same number as the board, and I've added a line on a queued ticket's page: "In line with F169, #1 in Planted". A bug shows its own place. The pages work it out from the list each time they open, so the number is always right. It's the card's place in line: a ticket that's waiting can still be passed over, and the fast lane still goes first.
>    Action: Open the mock-up, which now shows real cards from today's queue. Ticket f222-03 builds it.
> 2. **Why not store a rank in each card or ticket**: That's today's system with unique numbers, and it brings back what you asked me to retire. Dragging a card from the bottom to the top would rewrite every card in between. Each card that finishes would shift every card behind it, or the stored numbers would be wrong. Even with shared numbers, one of the last ten drags changed 30 files and another 17. With the list, a drag changes one file and you still see the number.
>    Action: I recommend no stored rank; ADR 45 item 7 now says so.
> 3. **Why a file rather than the main database**: A database-only order is workable: no file and no commit on each drag. I still recommend the file for three reasons. The runner picks work from the repo and is built to keep going if a database write fails, so a database problem could silently run work in the wrong order. The database is copied once a day, so losing it could lose up to a day of your drags, while a file in git loses none. And the cards and tickets are in git, so the order stays with them. The database still gets a copy, and that copy is what the pages read, so you lose no speed or display.
>    Action: Keep the file. If you'd rather accept those risks for the simpler database-only version, say so and I'll rewrite ADR 45 and f222-02; the cost stays about the same.
>
> Proposals:
> - ADR 45: The queue's order is one list, and the priority number goes (adr)
> - Where the priority number leaves the pages (mockup)
> - One queue list, and approved plans go to the end (plan)
