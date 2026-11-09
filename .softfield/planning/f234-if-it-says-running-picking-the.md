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
