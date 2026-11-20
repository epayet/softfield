# F278: A new project's M1 waits on the desk while its setup runs, not as a seed

The planning thread behind F278's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 16:12

> until the setup job picks up the work to make the first adr, the planning says to wait for m1. that's ok, but there's a seed of the first thing, which disappears after the setup starts. it's a bit confusing

## The lead, 2026-11-19 16:20

> I traced what the desk showed for duck-ascii-test and drafted a one-ticket fix.
>
> 1. **Why the seed was there, then gone**: When duck-ascii-test was made (16:04), M1 went on its board as an idea card with no thread yet. The desk lists any idea card without a thread under "Seeds, not asked about yet", so M1 showed there, while the strip above said the lead's setup was next in line. At 16:10 the setup job started and opened M1's thread. M1 stopped being a seed, but it didn't move to "Your answers wanted" either: that group only lists a thread whose last message is yours or the runner's, and this one had no message at all. So for two minutes M1 was nowhere on the desk, until the lead's first message at 16:12 brought it back.
>    Action: Fix it with the ticket in point 2.
> 2. **M1 waits under Your answers wanted from the start**: Fix: while a setup job is waiting or running, its card counts as a reply the lead owes you. From the moment the project exists, M1 shows under "Your answers wanted" with the dashed orange edge, saying "waiting for the lead · …". It switches to "the lead is writing this reply" once the job starts, then becomes the lead's reply. It is never a seed, and it never leaves the desk. A developer can build it: it touches the desk code only (factory_dashboard/planning.py), and the code already has an example to follow.
>    Action: Ticket f278-01-setup-card-waits-on-the-desk, in the plan.
> 3. **No mock-up**: There's no mock-up because nothing new is drawn. M1 uses the same dashed row that every message waiting for the lead already uses, only earlier and in one group instead of two. If you'd like to see it drawn anyway, say so and I'll make one.
>    Action: Nothing.
>
> Proposals:
> - F278: a new project's M1 waits on the desk while its setup runs (plan)
