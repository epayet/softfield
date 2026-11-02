# F184: The top bar's dot goes green while the runner checks, not grey

The planning thread behind F184's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 07:50

> When check all is running the dot in the header is grey like nothing is happening

## The lead, 2026-10-29 07:56

> This reply finds why the dot is grey and drafts a one-ticket plan with a mock-up.
>
> 1. **Why the dot is grey during check-all**: The dot only looks at jobs: orange for the lead, blue for a developer. Check-all, the gates, the warm-up and picking the next ticket aren't jobs. The runner just writes them as its current activity. So the bar reads "Running: check-all · …" but keeps the grey dot that means "no job" (factory_dashboard/app.py, factory_status). On a phone you only see the dot, so the factory looks stopped for several minutes after every ticket.
>    Action: Fix it with the ticket below.
> 2. **A green dot for the runner's own work**: I recommend a fourth dot colour rather than borrowing the ticket's agent colour. While check-all runs on a developer's ticket, the developer isn't working; the runner is. Check-all on main has no ticket at all. So the dot turns green and breathes like the agents' dots. Grey is left meaning only "nothing happening". Green is the colour you suggested for "doing a job" on F17, Tighter running and pause presence in the top bar. It is already a token (--good), so no new colour is added.
>    Action: Ticket f184-01-runner-dot (developer, small).
> 3. **Pausing during check-all says what it waits for**: Today, pressing ⏸ during check-all reads "Pausing after this job" with a grey dot. With this plan it reads "Pausing after check-all · <ticket>" and keeps the green dot. The words that show the moment you tap get fixed too: they would otherwise come out reversed ("f1-04 · check-all").
>    Action: Part of the same ticket.
> 4. **Mock-up**: runner-dot.html shows the top bar today and proposed, on a wide screen and a phone, during check-all on f172-07, Fast lane in the card. It also shows the pause-asked state and a key of every dot and what it means.
>    Action: Flip Today / Proposed. If green is too loud, say so and I'll tone it down.
>
> Proposals:
> - F184: a green dot while the runner works between jobs (plan)
> - F184 mock-up: the dot while the runner checks (mockup)
