# F147: What happens to parked work when Claude runs out

The planning thread behind F147's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-16 13:04

> What happens to checkpointing and WIP attempts that need directions when I'm out of Claude completely, is the work wasted?

## The lead, 2026-10-16 13:06

> Nothing is wasted. The runner parks the work and picks it up after Claude's reset, and the database shows it has done so before. This reply answers from the code and the numbers, and drafts nothing.
>
> 1. **A developer ticket waiting for its direction keeps its work**: Developers run locally, so their attempts don't need Claude. Only the lead's direction before the last attempt does. When Claude is out, the runner sets the ticket aside with its work so far: its branch, every attempt's thinking and the gate's output. The last attempt isn't counted as used, and the direction isn't counted either. After the reset, the direction reads all of it and the last attempt carries on from the same branch, with main merged in. This has happened 3 times in 42 directions so far.
>    Action: Nothing.
> 2. **A Claude job cut off mid-run is saved, then resumed**: If the limit hits while Claude is working (a lead ticket, a direction, a review), the runner commits what it has done so far on the ticket's branch as "wip … (parked)" and keeps Claude's session. The job starts again after the reset. Six lead tickets were stopped this way between Oct 1 and Oct 5. Five resumed and passed. The sixth was f1-53, the factory floor ticket, which was later taken out of the plan, not lost.
>    Action: Nothing.
> 3. **Checkpoints: Copilot covers them meanwhile, Claude checks again later**: When a checkpoint comes due and Claude can't take it, Copilot reviews the new merges read-only. Its findings become fix tickets straight away. Then the checkpoint waits for Claude, which checks those merges again once it can. Nothing goes unchecked, and Copilot's review counts for something meanwhile. This has happened twice in 28 checkpoints. F140, Copilot takes checkpoints first, would make Copilot do this even when Claude is free.
>    Action: Nothing.
> 4. **The queue doesn't stop**: While Claude is out, only the jobs that need it wait: lead tickets, directions, checkpoints, escalations and reviews. Developer tickets that need no direction keep running and merging on the local model. Support jobs also stop before the week's last share, which the runner keeps for you, so your planning questions here can still run when the automated jobs have stopped.
>    Action: Nothing.
> 5. **The one way work can be redone: a clash with main**: A ticket that waits a long time (a whole weekly limit) falls behind main while other tickets merge. When it starts again, the runner merges main into its branch. If the two clash, the runner starts the ticket fresh from main, and its earlier attempts are paid for again: local time only, no Claude money, and the direction still has their logs to read. The longer Claude is out, the more likely a clash is. I haven't seen this cost anything yet, so I wouldn't build anything for it now.
>    Action: Nothing now. The next factory review counts how often a parked ticket had to start again from main; if it happens, the fix would be a ticket that hands a clashing branch to its direction instead of starting from main.
> 6. **This card is a question, so it can be archived**: There's nothing to build. Once you've read the answer, the card can go.
>    Action: Archive F147 from its page once you've read this.

## The owner, 2026-10-16 20:39

> On point 2: is it the same for planner / planning questions and proposals reviews as well? just checking that if that is running out of tokens mid-way, it doesn't block the whole factory. it should just answer later? actually what happens to the work of the planner that ran out of tokens mid-way, is it working on a separate branch and can continue? or perhaps it's best to start from scratch again next time?
> On point 5: so if there is a clash, the work is thrown away? shouldn't the merger (probably the lead) maybe decide to do a conflict resolution instead? does it not do that?

## The lead, 2026-10-16 20:44

> Two of your questions led somewhere new. Planner jobs and reviews already park and resume like lead tickets. But a clash really does throw the work away today, so I've drafted one ticket to keep it.
>
> 1. **Planner jobs and reviews park the same way, and nothing else stops**: Yes, it's the same for your planning questions, the replies to your comments on proposals (these are planner jobs too) and milestone reviews. If Claude is already out when one is due, it waits for the reset and the queue goes on. If the limit hits mid-way, the job's row waits too, so it never blocks the factory, and it answers later. A planner job is also the last to stop: it may use the share of Claude kept for you, which the automated jobs may not. No planner job has been cut off yet: 119 ran and none parked.
>    Action: Nothing.
> 2. **A planner cut off mid-way carries on; it doesn't start over**: Its drafts so far are committed on the card's plan branch, plan/f147 here, as "wip (parked)". Its Claude session is kept. After the reset the same session goes on, told where its work is. I'd keep it that way rather than start from scratch: the resumed session still has what it read and its half-written drafts, so it doesn't pay twice to read the code and the cards again. The one cost is that after hours of waiting, Claude's cache has gone, so the resume re-reads the conversation at full price. That is still cheaper than doing all the work again.
>    Action: Nothing.
> 3. **A clash does throw the work away, and it's worse than I said**: You're right to push. Reading it closely: when a waiting ticket goes on and main has moved under it, the runner tries to merge main into the ticket's branch. If that clashes, it resets the branch to main and keeps no copy of the work. Worse, in this case the direction then sees an empty diff, and the last attempt isn't told its work was reset. It starts from main without knowing why. Nothing records a clash either, so I can't tell you how often it has happened. The longer Claude is out, the more likely a clash is. So I was wrong to say it wasn't worth building.
>    Action: Ticket f147-01: save the work before the reset, give it to the direction and the last attempt, and record each clash.
> 4. **Who resolves the clash: the direction decides, the developer redoes it**: I'd rather not add a separate job for the lead to resolve conflicts. It would be an Opus job of about $2–5 each, and it would be held back by the same Claude limit that made the ticket wait. A Claude job already runs at exactly that moment: the direction. So it gets the saved work, says what to keep, and the local developer reapplies it on top of the new main for free. The work is kept, and the lead still makes the call you asked for.
>    Action: Decision D1 in F147's doc. If you'd rather Claude did the merge itself, say so here and I'll change the ticket.
> 5. **F147 is no longer only a question: keep it, don't archive it**: My last reply suggested archiving the card. With this fix it now has a plan of one lead ticket, about 1 to 2 hours of the line. It runs after F106, Where do blocked tickets go, because both change how the runner handles a waiting ticket.
>    Action: Approve the plan below.
>
> Proposals:
> - F147: a clash with main keeps the work (plan)
