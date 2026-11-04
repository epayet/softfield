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

## The lead, 2026-10-28 09:53

> Approved by the owner on 2026-10-28: approved plan/f149: queued f149-01-reviews-stop-writing-a-backlog, f149-02-backlog-items-to-seeds

## The lead, 2026-11-02 20:54

> Done on 2 Nov: no review writes a backlog file, and Softfield's is gone. Items became bug-49 to bug-53, cards F200 to F202 and a line on F143; the rest are dropped with reasons, listed on this card. Travel Companion's and Coucou's files go through their own planted cards, F10 and F1.

## The owner, 2026-11-04 07:56

> rather than becoming a seed on my board, i imagined more of a 'plant this seed' option from the review, unless that is planned elsewhere already?

## The lead, 2026-11-04 08:07

> You're right, and it's only partly planned. I've drafted ADR 43 and one ticket that make a review's small fixes plantable from the review, instead of landing on your board.
>
> 1. **Half of this is already planned**: F164, Plant a review's ideas straight from the review, builds the plate with Plant and Plant and ask the lead. It's ready but not built, because its tickets f164-01, f164-03 and f164-06 are still waiting. It only covers ideas in "What next". Small fixes go to the board because I wrote it that way in ADR 35, No backlog file: the review sets a bug ticket aside without asking you.
>    Action: Build on F164's plate. No second button or new screen.
> 2. **A review's small fix becomes a line you can plant**: I agree with you. 52 bug tickets are set aside on Softfield's board, and the last 8 reviews added 5 more that nobody asked for. Now a review will write each small fix worth a run as one sentence in "What next": the file, the problem and the fix. It shows on F164's plate with the same two buttons, and nothing reaches your board until you press one. That's about one plate per review going by those 8.
>    Action: ADR 43 and f164-07, review fixes are quoted too.
> 3. **The cost: a planted fix isn't ready to run**: A set-aside bug ticket can be queued as it is. A planted fix is only an idea card, so it needs Plant and ask the lead to get its ticket, and that planner job has averaged $2.40. You pay only for the fixes you want, and reviews stop writing tickets nobody asked for, so I still recommend it. The cheaper-looking option, where Plant releases a ticket the review already wrote, means paying for every ticket whether you plant it or not, plus a new kind of request.
>    Action: Nothing, unless you'd rather keep ready-made tickets.
> 4. **The risk: a fix nobody plants stays in its review**: An unplanted fix stays only in the review report and the metrics database, and nothing reminds you of it. Bugs in the milestone's own work are still fixed without asking, and a security finding can never be left as a line to plant.
>    Action: Written into ADR 43, items 3 and 5.
> 5. **Fixes must land on the right project's board**: F164 sends any line under Factory to Softfield's board. A fix to Stampu's own code written there would be planted in the wrong project, so a project's own fixes go under Product. Softfield's own fixes go under Factory.
>    Action: Written into ADR 43, item 2, and f164-07, review fixes are quoted too.
> 6. **Reviews keep setting bug tickets aside until F164 is built**: Without the plate, a quoted line has no button, so f164-07, review fixes are quoted too, waits for F164's tickets. Until then reviews keep setting bug tickets aside as they do now. F164, Plant a review's ideas straight from the review, is at 12 on the board.
>    Action: Drag F164 up if you want this sooner.
> 7. **The 52 bug tickets already on the board stay**: They're already written and paid for, and any one of them can be queued as it is. Turning them into plates would cost money and fix nothing. You can still remove any you don't want from the board.
>    Action: Nothing.
> 8. **F149 can still be signed off**: The new ticket sits on F164, because that's the work it waits for. Sign-off refuses a card with tickets left, so a ticket here would have held F149, Retire the backlog file, until F164 was done. The backlog file itself is retired as you asked. Only the bug-seed part of the sign-off sheet changes later.
>    Action: Press Accept on ADR 43, then Approve, then Sign off on this page. Approve is refused until ADR 43 is accepted.
> 9. **No new mock-up**: A fix looks exactly like an idea on F164's plate, so F164's mock-up already shows it. Nothing else changes on screen.
>    Action: Tell me if you want fixes to look different from ideas, and I'll draw it.
>
> Proposals:
> - ADR 43: The owner plants a review's small fixes (adr)
> - F164: a review's fixes get Plant buttons too (plan)
