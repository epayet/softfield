# F276: The top bar's dot and words see the lead's setup jobs

The planning thread behind F276's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-19 16:07

> i don't think the dot at the top knows about setup jobs

## The lead, 2026-11-19 16:10

> You're right about the pause. While you hold the factory, the runner still runs setup jobs, but the dot only lights for a planner job, so the bar says "Paused by you" with no dot while the lead sets up a project. I've drafted one developer ticket (f276-01) and filled in the card doc, both on `plan/f276`; the ticket passes the ticket check.
>
> 1. **You're right, while the factory is paused**: The runner runs setup jobs even while you pause the factory. But the top bar only checks for a planner job: a setup job running during your pause leaves the bar saying "Paused by you since …" with no dot, as if nothing were running. When the factory isn't paused, a running setup job does light the lead's dot.
>    Action: Ticket f276-01: during a pause, a setup job lights the lead's dot and the bar reads "Paused by you since 11:40 · the lead is setting up duck-ascii-test". If the lead is also answering you, that wins.
> 2. **The words show internal names**: A lead job with no ticket shows its internal role and job number. The bar says "Running: softfield · planner, job 2502" right now, and a setup job would say "setup, job N".
>    Action: Same ticket: "Running: the lead is setting up duck-ascii-test" and "Running: softfield · the lead is answering you".
> 3. **With several projects paused, the wrong one can show**: During a pause every project counts the same, so the bar shows the first one in the Projects order, even when the lead is working on another one further down.
>    Action: Same ticket: the project where the lead is working is the one the bar shows.
> 4. **duck-ascii-test's setup hasn't started yet**: Its setup job was queued at 16:04 and was still waiting at 16:08. The runner put two answers to you on Softfield's cards first (F275 and this one), because answers go before setup jobs (ADR 48 item 4). The bar shows what is running, and the project's plate says "Asked", so nothing is wrong on screen. It just means a new project waits for any answer the lead is writing.
>    Action: Nothing, unless you'd rather a project you just started go before answers: then I'll draft a change to ADR 48 item 4.
> 5. **No mock-up**: Only the words change, plus a dot the bar already has. Nothing moves and there is no new colour.
>    Action: Nothing; ask if you want one.
>
> Proposals:
> - F276: the top bar sees setup jobs (plan)
