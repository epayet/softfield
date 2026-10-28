# F149: Retire the backlog file: reviews stop writing it, its items become seeds

The planning thread behind F149's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Factory reviews still seem.to write to it. Plant seeds for every item if relevant then delete it for all projecs and ensure it stops getting written   since We have a ticket to be a le to plant suggestions from reviews we won't need the backlog file

## The lead, 2026-10-27 09:28

> I've drafted ADR 35 and two lead tickets that stop every project's reviews from writing `docs/backlog.md` and turn Softfield's items into bug seeds and cards. I'm pushing back on one card per item. ADR 35 must be accepted before Approve goes through.
>
> 1. **Yes, every project's review still writes it**: Nothing on the dashboard shows docs/backlog.md, but three things still send findings to it. The review prompt says "nits and should-fix points about untouched code go to docs/backlog.md". A re-review is told twice to put new points "in the backlog". docs/workflow.md has the same rule. The prompt is the factory's own, so it reaches every project: Softfield's file holds 30 items, Travel companion's 17 (from five reviews between 20 and 22 October) and Coucou's 18.
>    Action: f149-01 rewrites the prompt, the re-review wording and the docs, and adds a test that fails if a prompt ever mentions a backlog again.
> 2. **Not one card per item: fixes become bug seeds**: A card for every item would add about 65 cards across the three projects, mostly one-line nits, on top of the 36 ideas already on the board. The board already has a card for a small fix: a bug ticket set aside, shown as a seed, as bug-05 to bug-47 are since 23 October. My split is: fixes become bug seeds, real ideas become planted cards, and "only if it ever happens" notes are dropped. Dropped notes aren't lost, because each one stays in its review report.
>    Action: Built into ADR 35 and f149-02.
> 3. **F164, Plant a review's ideas straight from the review, covers ideas only**: F164 adds a Plant button to the ideas in a review's "What next". The nits and fixes that went to the backlog still need a place. From now on the review writes them itself, as bug tickets set aside on the board. A nit not worth a run is said once, in the review report, and nowhere else.
>    Action: ADR 35, items 1 to 3.
> 4. **Accept ADR 35 before you approve the plan**: Where review findings go is a workflow rule, and those change only through an accepted ADR. f149-01 names ADR 35, so Approve refuses the plan until the ADR is accepted.
>    Action: Press Accept on ADR 35, then Approve on the plan.
> 5. **What happens to each of Softfield's 30 items**: Bug seeds (3): the two timing tests that fail now and then (f90), the checkpoint restarted on every merge (f151), and a test that opens every page and fails on escaped HTML (f158). New cards (2): "where the hours went" in the review report (f53), and ticket and card pages showing formatted text instead of raw markdown (f159). Already covered elsewhere (3): bug-01, bug-03 and bug-40. Dropped (9 notes): races a few seconds wide that have never happened, harmless leftovers, and two gates turned down for low ceremony. The Coucou section is already in Coucou's own file. Every one of these choices is listed in the card's D4.
>    Action: f149-02 checks each item against the code, writes the seeds and cards, then deletes the file.
> 6. **Travel companion and Coucou: one plant on each board**: A Softfield ticket can't write into another project's repo, so each of those projects cleans up its own file through a card on its own board. Pick the project in the Plant box and paste:
>
> Travel companion: "Retire docs/backlog.md: a lead ticket writes each item still worth a fix as a bug ticket set aside in .factory/tasks/later/ (milestone: bugs, finding: the review's id, its words and fix in full), drops the rest with a reason, then deletes the file. Reviews no longer write it."
>
> Coucou: "Retire docs/backlog.md: a lead ticket writes each product item still worth a fix as a bug ticket set aside in .factory/tasks/later/, none queued while product work is on hold, drops the factory items Softfield already handles (m0, the m1 runner status, the 2026-10-02 sign-off) and fixes the links in README.md. Reviews no longer write it."
>    Action: You plant the two notes. Each project's lead then drafts its own single ticket.
> 7. **Until f149-01 merges, reviews keep writing the file**: This is two lead tickets, about an hour of work. F149 sits at the bottom of the board (priority 100), so any reviews that run before it will still add items. f149-02 converts whatever has been added by then. No ready ticket changes, so there's no need to pause the factory.
>    Action: Drag F149 up the board if you want the file gone before the next reviews.
>
> Proposals:
> - ADR 35: No backlog file: fixes are bug seeds, ideas are planted (adr)
> - F149: retire the backlog file (plan)
