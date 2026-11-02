# F179: Sonnet as the lead on easy tickets: how it does, what it saves, in reports

The planning thread behind F179's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-29 18:56

> Plan this card.

## The lead, 2026-10-29 20:30

> The trial ADR 32 asked for after about 15 Sonnet lead tickets is due: Sonnet has done 18. Below are its results, then a plan to put them in the reports.
>
> 1. **How Sonnet is doing as the lead on easy tickets**: Well. Since 23 Oct, Sonnet has done the 18 lead tickets of difficulty 4 or below. 17 merged on the first attempt. The 18th (f90-01) needed one Opus step-up, and that was a flaky test, not Sonnet's code. Its 6 'failed' jobs were all parked by Claude's limit, not real attempts.
>    Action: Nothing: the numbers are in the card doc's 'What we know'.
> 2. **How much it saves**: About $21.80 in six days, 65%. Sonnet's 18 tickets cost $11.66 including the Opus step-up, $0.65 a ticket. At Opus's own price for lead tickets of the same difficulty ($0.61 at 2, $1.69 at 3, $2.27 at 4), they would have cost about $33.47. At this pace that is roughly $25 a week. It also uses less of the 5-hour window that Opus and Sonnet share.
>    Action: Nothing to do now: tickets 01–03 put this number on the dashboard and in the reviews (point 4).
> 3. **The catch: more review findings, so keep the line at difficulty 4**: On Sonnet's 14 reviewed tickets, the milestone reviews found 7 should-fix problems and none that blocked: 5 per 10 tickets. Opus on tickets of the same difficulty: 2.1 per 10. Opus on its harder tickets: 4.1 per 10, plus 1 blocking. The problems were small (a name shown twice on the desk, a missing test, a guard that refused too much), and each was fixed in its review. Even so, Sonnet's work needs twice the fixing on the same tickets. Giving it difficulty 5 and up would put that rate on harder, protected code. I recommend keeping the line at 4 (no change to the config), not widening, and looking again at 40 Sonnet tickets using the new panel. The other choices are widening to every lead ticket, or going back to Opus for all of them (`lead_first_up_to = 0`).
>    Action: Card doc D8. Answer only if you want to widen it or go back.
> 4. **None of this is in the reports today**: The milestone review's Numbers give dollars per agent but nothing per model on lead tickets, and no saving. The Agents page's 'Who did what' has no lead-ticket column and no planner column, so Sonnet's 25 lead-ticket jobs and Opus's 153 show nowhere. F59 (A weekly report page) counts dollars by role, not by model. Fix: a single function works out the split and the saving (01). The Agents page gets a 'Lead tickets, by model' panel and every missing role column (02). Each milestone review's Numbers get a 'Lead tickets by model' table, with the saving to date (03). The weekly report's brief carries the week's split, so its read says how Sonnet did (04).
>    Action: Plan: 4 tickets. 01 and 02 go to a developer. 03 and 04 are mine because they touch protected files. At difficulty 3, Sonnet will build those two, the setup this card is asking about.
> 5. **Mock-up of the Agents page**: Today next to Proposed, on real numbers. A plate shows '$21.81 saved by Sonnet', with two bars to scale ($33.47 Opus would have spent, $11.66 Sonnet spent). Under it, a table: Sonnet at difficulty 4 or below, Opus at the same difficulties, Opus at 5 and up. For each: merged, first time, step-ups, dollars a ticket, and should-fix per 10 reviewed. 'Who did what' gains lead-ticket and planner columns. The bars use the Opus and Sonnet colours because they show those agents' dollars. Everything else is the usual plate ornament.
>    Action: Ticket 02 names the mock-up as the picture to build.
> 6. **The weekly report waits for F59**: The weekly report is F59's (A weekly report page). Its page and its weekly job are still in the queue. Ticket 04 waits for that job (f59-03), then adds the split to its numbers and its brief. I added no tile to F59's page: the written report covers it, and a tile can follow once the page exists and you've seen it. F167 (Is the split between local developers and the lead smart and cheap?) is related but asks about local developers, so it stays separate.
>    Action: Ticket 04, after f59-03. Nothing else.
>
> Proposals:
> - F179: Sonnet's lead tickets and their saving, on the Agents page and in the reports (plan)
> - Agents page: Lead tickets, by model (mockup)
