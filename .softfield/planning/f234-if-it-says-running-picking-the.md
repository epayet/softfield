# F234: The bar says "picking the next ticket" only while the runner is really picking

The planning thread behind F234's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-06 19:38

> If it says running picking the next ticket, but is actually not doing anything, it's not picking up tickets it should be clearer and the dot should not be green

## The lead, 2026-11-09 16:18

> I traced the bar's words to the runner and drafted a two-ticket fix with a mock-up. The two problems `softfield check-tickets` reports are in F9's drafts; both F234 tickets pass.
>
> 1. **Why it says "picking" while nothing happens**: Two of the runs are stuck on those words. travel-companion's run and coucou's have both said "picking the next ticket" since Nov 5 16:56, and neither has run anything since. When the runner works through several projects, each round starts by giving every project a turn for its queued jobs only. That turn writes "picking the next ticket" first, and if it runs nothing it leaves those words in place. Only a later ticket turn replaces them with the reason the project waits, and a project doesn't get that turn when an earlier project ran something. The top bar puts any "Running: …" line above an idle line (F132, The overview shows the whole factory), and F184 (The top bar's dot goes green while the runner checks) made that line green. So whenever softfield is between jobs, you see "Running: travel-companion · picking the next ticket" with a green dot.
>    Action: Ticket f234-01 (the lead, because it changes runner/): a turn that runs nothing always ends by saying why the project waits, for example "Idle: 2 tickets wait for their turn". The dot goes grey.
> 2. **A guard for a runner that really hangs**: This goes further than you asked, so you may not want it. The heartbeat runs on a thread of its own, so a runner whose main loop hangs still looks alive and keeps its last words forever. Picking normally takes a few seconds. I propose that the run records since when it has been doing what it says. Past 5 minutes on "picking the next ticket", the bar says "No progress since 16:02 · picking the next ticket" with a steady yellow dot that doesn't breathe. Check-all and the gates are left out on purpose: they can rightly take a long time.
>    Action: f234-01 adds the time to the run's record, and f234-02 (a developer, following F184's dot) draws it in the bar. If you think point 1 is enough, say so and I'll drop f234-02.
> 3. **Mock-up**: Today shows the green "Running: travel-companion · picking the next ticket" on a wide screen and a phone, plus a runner that has hung. Proposed shows the grey idle line with its reason, the yellow "No progress since…" state, and the key to the dots with its new entry.
>    Action: .softfield/cards/f234-mockup/stuck-picking.html, named in f234-02's Context. The before-and-after pictures are of / and /planning.
> 4. **Not a repeat of F132**: F132 (The overview shows the whole factory) already makes the bar follow a live job, and it is the card where you first saw this message. But it never stopped a stale "picking" from showing when no job runs. Its open ticket f132-02 would also show that stale line under Now. F234 fixes where the words come from, so both cards benefit and nothing needs merging.
>    Action: Nothing to do.
>
> Proposals:
> - F234: the bar says "picking the next ticket" only while the runner is really picking (plan)
> - F234 mock-up: "picking the next ticket" only while it picks (mockup)

## The owner, 2026-11-09 16:31

> I sent back your proposal “F234 mock-up: "picking the next ticket" only while it picks” (stuck-picking-mockup).
> - On its key point 1 (Listed by the runner): No progress for 5 minutes is too close to the lead orange yellow

## The lead, 2026-11-09 21:01

> I changed the "no progress" dot and its words from yellow to red, in the mock-up, the card and the ticket. All three F234 tickets pass pre-flight.
>
> 1. **The stuck dot is now red, not yellow**: Agreed: next to the lead's orange dot and the orange waiting ring, the hazard yellow was too easy to mistake. The "No progress since 16:02 · picking the next ticket" state now has a steady red dot and red words. No other dot uses red, and it reads as "something is wrong", which is true when the runner has hung. Grey wouldn't work: grey already means idle, and a stuck runner is the one case you need to notice.
>    Action: The mock-up's Proposed side, the card's D3 and the dashboard ticket now say red. The dashboard ticket is renamed f234-02-stuck-picking-in-red.
> 2. **An old draft has to be removed, and the lead's ticket does it**: A planning job can't delete files, so the earlier yellow draft (f234-02-stuck-picking-in-amber) stays on the plan branch beside the red one. On Approve both would be queued. The yellow one now waits until the red one is done. It is also marked as replaced and says to change nothing if it is ever picked. f234-01 runs first and is the lead's, so it deletes the yellow draft as part of its own work.
>    Action: Nothing for you to do: f234-01 lists the deletion among its steps and its acceptance checks.
>
> Proposals:
> - F234 mock-up: "picking the next ticket" only while it picks (mockup)
> - F234: the bar says "picking the next ticket" only while the runner is really picking (plan)

## The lead, 2026-11-09 23:05

> Approved by the owner on 2026-11-09: approved plan/f234: queued f234-01-turn-says-why-it-waits, f234-02-stuck-picking-in-amber, f234-02-stuck-picking-in-red

## The lead, 2026-11-16 19:28

> Merged F244 here: the dot is green at the top sometimes it says picking up…

## The owner, 2026-11-16 19:28

> From F244, merged here:
> the dot is green at the top sometimes it says picking up the next ticket where clearly it's working on something right now, seems like a bug. it's happened a few times i had to ask why is the factory doing nothing, and the reply was usually 'what do you mean, it is doing something right now' but that's not what the dot says. separately, the command line sometimes say 'nothing to do' multiple times in a row in between things it actually has to do very shortly

## The lead, 2026-11-16 19:36

> I've reworked F234's first ticket to also stop the repeated "Nothing to do." lines, which needs your approval as a change to its ready tickets. The cause of the wrong green dot is confirmed on the live runs right now.
>
> 1. **The green "picking the next ticket" while it works: confirmed right now**: While I write this, softfield's run is answering you, but coucou's, travel-companion's and coaster-ranker's runs have all said "picking the next ticket" since the runner started at 19:17. None of them is doing anything. Whenever softfield is busy with something other than an agent's job, such as check-all, the gates or a merge, the top bar takes the first project in order that says "Running: …". That is one of these stale lines, shown with a green dot. So the words describe a project that is doing nothing, while the work goes on in another one. This is exactly what F234's first ticket fixes: a project that ran nothing in its turn ends on its real reason ("Idle: …", grey dot), so the bar shows what softfield is really doing.
>    Action: Nothing new to decide: f234-01 already covers it (D1).
> 2. **The repeated "Nothing to do." in the terminal**: Each project has its own session in the runner. When the runner restarts (after a merged lead ticket, a review or a new day), it closes all of them. Each session that ran nothing prints "[runner] Nothing to do." without naming its project. With four projects, that is up to three of those lines in a row, just before the work starts again. They're true but useless. I'd drop them when the runner works across several projects; the database still records each of those runs as "nothing to do". A single project's run keeps the line, because there it is the whole answer.
>    Action: Added as D5 to F234's first ticket (f234-01, the lead's), in the change below. It is the same file and the same kind of fix, so I kept it as one ticket rather than a new one.
> 3. **Move F234 up the board so the fix arrives**: F234 is approved but sits at 100 on the board, behind about 50 cards. At about 27 minutes a ticket, that is many days away, and you have already lost several questions to this bug. Its two tickets are small and depend on nothing else.
>    Action: Drag F234 up on the board, right under F245 ("I accepted a plan as go"). The runner picks the new order up at its next pick.
> 4. **Pause before approving? Not needed**: This changes a ticket that is already in the queue. It can only start once F234 is near the top of the board, so it won't start while you read this. If you drag F234 up first, pause the factory from the top bar before you approve; approving the change lifts the pause.
>    Action: Approve the change below, then drag F234 up.
>
> Proposals:
> - F234: f234-01 also stops the repeated "Nothing to do." lines (replan)
