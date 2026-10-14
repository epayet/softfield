# F26: I want to see numbers next to "Coming" and "Your desk" to have a sense of how many there are

The planning thread behind F26's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-07 23:08

> I want to see numbers next to "Coming" and "Your desk" to have a sense of how many there are

## The lead, 2026-10-07 23:25

> I've drafted the plan and one small ticket. Here's my reply.
>
> 1. **Is this a repeat?** No. No other card or thread asks for counts on the planning page. The nearest is F19 ("will I need to refresh planning"), which is about keeping the page up to date, not about numbers. The Planning tab already shows the desk's number ("Planning · 5"); it was added in f6-09. The headings just don't show it yet.
>
> 2. **What you'll see.** The headings will read "Coming · 2" and "Your desk · 5". That's the same style as "Archived · 3" on that page and "Planning · 5" on the tab. The desk's number is the same total the tab uses, so the two always agree.
>
> 3. **Nothing at zero.** An empty desk keeps "Your desk" with no number, because "Nothing waits for you." already says it. "Coming" stays hidden when nothing is on its way, as it does today.
>
> 4. **Totals only, not one number per group.** I recommend showing no count on the four groups inside the desk ("Your answers wanted", "Proposals to review", …). Each group lists its items right under its name, so a number would repeat what you can already see. If you'd like the split anyway, the other option is "Proposals to review · 2" and so on, for about the same small cost.
>
> 5. **One catch: the numbers don't update on their own.** The numbers are shown when the page loads, along with the lists. On an open page, the tab's number refreshes by itself but the headings won't until you reload, so for a moment they can differ. I'm leaving that to F19, which is already about refreshing the planning page, rather than patching it here.
>
> 6. **Who builds it and when.** It's one small developer ticket, `f26-01-desk-counts`, of difficulty 2. It follows the Archived heading in the same template. I've set the card's priority to 6, which puts it just after the work already planned (F20/F21 at 1, through F10 at 5). If you'd rather have it sooner, I'd suggest 3, alongside the board work. The ticket also touches the planning page that `f9-28` changes, but that's a small, separate change. This plan doesn't touch any queued ticket, so there's no need to pause the factory.
>
> 1. **Not a repeat**: No other card or thread asks for counts on the planning page. F19 is about refreshing the page, not about numbers. The Planning tab already shows the desk's number (f6-09); the headings just don't show it yet.
>    Action: nothing
> 2. **What you'll see**: 'Coming · 2' and 'Your desk · 5', in the same style as 'Archived · 3' and the Planning tab. The desk's number is the same total the tab uses, so the two agree.
>    Action: ticket f26-01-desk-counts
> 3. **Nothing at zero**: An empty desk keeps 'Your desk' with no number, because 'Nothing waits for you.' already says it. Coming stays hidden when empty.
>    Action: in the ticket
> 4. **Totals only, not one number per group**: I recommend no count on the four groups inside the desk: each lists its items right under its name. The other option is 'Proposals to review · 2' and so on, for about the same small cost.
>    Action: in the ticket; tell me if you want the per-group numbers
> 5. **The numbers don't update on their own**: The numbers are shown when the page loads, along with the lists. On an open page, the tab's number refreshes by itself but the headings won't until you reload, so for a moment they can differ. That belongs to F19, which is about refreshing the planning page.
>    Action: nothing here; F19 covers it
> 6. **Who builds it and when**: One small developer ticket (difficulty 2) that follows the Archived heading. The card's priority is 6, just after the work already planned (F20/F21 at 1, through F10 at 5); 3 would bring it in alongside the board work. No queued ticket is touched, so there's no need to pause the factory.
>    Action: plan proposal f26
>
> Proposals:
> - F26: numbers next to Coming and Your desk (plan)

## The owner, 2026-10-13 00:01

> I want numbers next to Proposals to review and and your answers wanted, and other similar sections too

## The lead, 2026-10-13 00:02

> Each desk group gets its own number: I've drafted one small ticket and updated the card's plan; the ticket passes pre-flight.
>
> 1. **Every desk group gets its number**: Agreed, and it reverses my earlier "totals only" choice. The five groups on your desk will each read like "Proposals to review · 2": "Didn't go through", "Your answers wanted", "Proposals to review", "Finished, to talk through" and "Seeds, not asked about yet". "Coming", "Your desk" and "Archived" already show theirs.
>    Action: ticket f26-02-group-counts
> 2. **A group's number can be smaller than the cards under it**: Each number counts what still waits for you, the same rule "Your desk · N" and the Planning tab use today. A card you've already acted on (archived, signed off, seed removed) stays listed with a dashed edge until the runner's next pick, but is no longer counted. This way the groups' numbers add up to the desk's number. The other option is to count every card shown, but then the groups would add up to more than the desk says. I recommend the first.
>    Action: in the ticket; tell me if you'd rather count every card shown
> 3. **No number when a group has nothing left for you**: A group holding only cards on their way shows its name alone, as "Your desk" does when nothing waits. Empty groups stay hidden, as today.
>    Action: in the ticket
> 4. **It goes after F63, I want to see cards in order**: That card's ticket (f63-01-desk-order) reorders the same groups and renames "Finished, to talk through" to "To sign off". Building this one after it avoids two tickets changing the same lines and tests written against a name about to change.
>    Action: f26-02-group-counts waits for f63-01-desk-order
> 5. **I raised this card's priority from 6 to 2**: At 6 it would run after nearly all of the 60 ready tickets, at about 53 minutes each: several days of running. At 2 it sits with the other planning-page fixes (F13, F22, F63…) and goes right after f63-01-desk-order. It is one developer ticket of difficulty 2.
>    Action: in the plan; say so if you'd rather keep it at 6
>
> Proposals:
> - F26, numbers on the desk: each group gets its own (plan)
