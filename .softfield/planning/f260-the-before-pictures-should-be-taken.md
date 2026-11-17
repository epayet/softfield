# F260: Before pictures on the data kept from just before the card's first merge

The planning thread behind F260's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-17 19:48

> The before pictures should be taken on a copy of the database from before the milestone's first merge (or at plan approval), so a milestone that drops a column still gets its before pictures. From F222's review.

## The lead, 2026-11-17 19:54

> I've drafted a plan for F260, "Before pictures on the data from before the card": two tickets, plus an amendment to ADR 40 (Before and after pictures at sign-off). I recommend one change to your idea, below.
>
> 1. **Why F222's before pictures failed**: Each review copies the live metrics database once and draws both the before and the after pictures on that copy. The live database had already been migrated by F222's code, which dropped `milestones.priority`. So the old code asked for a column that was gone, and every before page answered 500. A project that uses sample data has the same problem: its `prepare` runs on main's code, so its data follows main's database layout too.
>    Action: Fixed by the plan below.
> 2. **When to keep the data: just before the first merge, not at plan approval**: Approval can come weeks before the work starts, and other cards' changes land in between. Softfield's database would cope with that, but a project like Coucou (sample data, Django) might not: data made then could be too old for the code at the card's start. Just before the card's first ticket merges, main's code is exactly the before code. So the runner runs `prepare` once at that moment, in a copy of main, and keeps the folder until you sign the card off. This only happens for a card that lists pages in its doc, in a project with `[shots]`. If it fails, it never stops the merge.
>    Action: Ticket f260-01.
> 3. **My pushback: use the kept data only when today's data fails**: If every before picture used the kept data, before and after would show data from different days. F222's would be 5 Nov against 17 Nov: different cards on the board and different counts. You'd see changes the card didn't make. ADR 40 turned down 'take the before when a card starts' for this reason. So I recommend: draw the before on today's data first, as now. Only the before pictures that fail are taken again, on a copy of the kept data, and those say so. Your version (always use the kept data) is simpler by a few lines. It also guarantees the before matches the old layout even when a page still loads but draws wrong. Recommended: the fallback.
>    Action: Answer only if you want 'always the kept data'. Otherwise the fallback is built (D2).
> 4. **The page says which day a before was drawn on**: A before picture taken on the kept data gets the caption 'Before · at the card's start, on the data of 5 Nov'. Other before pictures keep today's caption. The review is told the same thing, so it doesn't count different numbers as the card's change. I drew no mock-up: only the words of an existing caption change.
>    Action: Ticket f260-02 (developer), and the review's part in f260-01.
> 5. **Cost**: Once per card with pages: `prepare` runs at its first merge, up to a few minutes. For Softfield it is one copy of the metrics database kept on this machine until sign-off, never in git. The sign-off deletes it. At a review, the extra round runs only when a before picture fails.
>    Action: None.
> 6. **ADR 40 gets an amendment**: This partly brings back an option ADR 40 turned down (taking the before when a card starts), as a fallback only. I added a dated amendment to ADR 40 on this branch. It lands when you approve the plan.
>    Action: Approve with the plan.
>
> Proposals:
> - F260: before pictures on data kept from before the card (plan)
