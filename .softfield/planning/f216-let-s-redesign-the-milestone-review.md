# F216: A shorter, consistent review page, with the decisions made along the way

The planning thread behind F216's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-04 07:52

> Let's redesign the milestone review page it's very inconsistent and long to read. The decisions from you is always either empty or not very interesting (just says what adr was involved). I prefer a 'decisions I made along the way' or similar especially if it's decisions it took that were not thought of during planning that the model thought was a good idea. Separately, I wonder if the reviews are currently expensive to run to write this kind of reports? Let's make sure it's useful if it's rich

## The lead, 2026-11-04 08:04

> The three tickets pass the check, and I couldn't open the mock-up in a browser from here. The two problems the full check lists belong to set-aside F9 tickets, not this card.
>
> 1. **Are reviews expensive?**: Moderately, but the report isn't what costs. A review job averages $1.82 on Opus: $216.54 of $1,353 on Claude so far (16%), and 19% since 20 October. Planner jobs cost more, at $575 (43%). The last 15 cards averaged $3.04 of review each, 31% of what those cards cost. Writing the report takes about a tenth of a review at most: on F187 it was about 3,500 of 48,296 written tokens (my estimate from its length), plus 9 database queries among its 100-odd tool calls. The rest goes on reading the diff and fixing what it finds.
>    Action: This plan puts each review's cost on the card's page, in What it cost.
> 2. **Is the money well spent?**: Yes, on the code reading; less so on parts of the report. Reviews have fixed 173 blocking or should-fix findings themselves, including F187's two bugs that would have started on 28 March. Even cards of 1–2 tickets get 1.4 such findings each for $1.67, and only 8 of 46 reviews found none. So I'd keep Opus reviews on every card, small ones too. I'd cut the report: its second half appears on no page, and its per-session lines repeat what the runner already holds. That saves little money, under a tenth of a review, but it makes the report much shorter to read.
>    Action: No change to who reviews. The report shrinks (points 4 and 5).
> 3. **Could a cheaper review work on small cards?**: I'd say not yet. Sonnet would cut the bill, but we have no evidence of what it would miss, and the one number we have points the wrong way: its own tickets draw twice Opus's findings (F179, Sonnet as the lead on easy tickets). Small cards would save about $1 each, and a missed bug costs more than that.
>    Action: Nothing now. If you want the saving anyway, I'd draft an ADR for a trial with both models reviewing the same cards.
> 4. **Decisions made along the way**: You're right about the section: 79 of the 88 stored sheets start "None", and most of the others just name an ADR already settled. The material you want already exists, but in the part of the report no page shows. F187's changes outside the plan are one example, and they make the three decisions in the mock-up. The new section lists what the plan didn't decide: what was chosen, why, the other option and who chose it. There are at most 5 entries, and with none the section doesn't show. Anything that really needs you stays separate, as Needs your answer, straight under the head.
>    Action: Tickets 01 and 03.
> 5. **A shorter, consistent page**: The inconsistency has two causes. Some parts are themed plates and others are bare sections, and `_to_html` can't render numbered steps, nested bullets, backticks or links, so raw `[session](…)` text reaches the page. The new page has one kind of plate and reads in this order: what it's about, what changed, before and after, how to test, decisions made along the way, Sign off, What next. Everything else folds into one plate, and each fold says what's inside. Sign off moves below the review, so you read before you press.
>    Action: Tickets 02 and 03; the picture is the mock-up.
> 6. **Two additions you didn't ask for**: Done when, as of now: each Done when line says Met, Not yet or Your check, in place of repeating the plan. It's the expected-against-actual you asked for first, and reviews already write some of it where no page shows it. What the review caught: the findings themselves with what happened to each, in place of the same counts shown twice. It costs nothing to write because the database already holds them, and it shows what the review's money bought.
>    Action: Both are in the plan. Tell me if either should go.
> 7. **A risk: decisions the review can't see**: The review works out these decisions by comparing the plan with the diff. It will miss a choice that left no trace, such as an option a worker considered and rejected. Asking every worker to report its choices would catch more, but it adds a step to every ticket, and local developers often drop such instructions. I'd start with the review alone: F187 and F175 show there is plenty to find. If three reviews come out thin, we add the worker step.
>    Action: Noted under Later on the card.
> 8. **This waits for F164, and F200 stays separate**: F164, Plant a review's ideas, changes the same prompt lines, `_to_html` and page, so all three tickets wait for its tickets and keep its Plant buttons in What next. F200, Where the hours went, would stop reviews writing their own queries for What clogged the line, so it's the other small saving. It isn't needed for this plan, so it stays its own card.
>    Action: If you want that saving soon, drag F200 up the board.
> 9. **Old reviews**: The 88 stored reviews aren't rewritten, because that would cost money for little. They get the new layout and the fixed text straight away, and their "None…" sections go. They just won't have the two new sections. F127's "None" also carried a note about ADR 41, which leaves the page but stays in its report file.
>    Action: Nothing to do.
>
> Proposals:
> - The card's page with its review: Today and Proposed, on F187 (mockup)
> - F216: a shorter, consistent review page, with the decisions made along the way (plan)
