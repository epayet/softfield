# F219: Lead tickets follow Claude's week pace; runner and dry run share one rule

The planning thread behind F219's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-04 20:54

> Lead tickets don't wait on Claude's week pace line, but --dry-run says they do. Decide which rule holds, then make the runner, --dry-run and the pages agree.
>
> Seen on 2026-11-04: Claude's week was 61% used, with a pace line of 32%. `softfield run --dry-run` listed bug-59 and the other lead tickets as "week 61% used, over its pace line of 32%", yet the runner picked bug-59 (job 1781). The lead told me it would wait, because it trusted the dry run.
>
> What the code does (read in live at b39bf5d3):
> - Real pick: `_next_task` in runner/loop.py holds a lead ticket only through `_waits_for_the_owner` and `_at_the_reserve`. `allowance.reserve_only` is true only when the job would dip into the reserve, which starts at 70% of the week with `reserve = 0.3`. A fast lane card or the reserve switch gets past it.
> - `work_queue` then calls `dispatch.pick(rows, tickets, dispatch.Windows(), now(), ...)` with empty windows, so that final check sees no allowance. This dates from f8-03 (2026-10-06).
> - `_lead_route` calls `router.route` with no windows, so routing doesn't pace a lead ticket either.
> - Dry run: `dry_run_plan` builds `dispatch.Windows` from the stored readings, and `dispatch._claude_says` asks `allowance.answer`, which applies the pace line.
> - ADR 25 says a job may start only under the pace line, so the real pick goes against an accepted ADR for lead tickets.
>
> Please check:
> - Whether the Coming, Overview and factory line pages show the same wrong wait. factory_dashboard/coming.py, overview.py and line.py use the dispatch code, but nobody has looked at what they show.
> - Whether lead tickets were paced for real before f8-03, or only in the dry run. ADR 25's evidence is a dry run from 2026-10-06, and it may have been misread the same way.
> - What else the pace line should still govern. Developer jobs on cloud agents are paced through `router.route`, and that should keep working.
>
> The decision for me, as an ADR item with your recommendation:
> 1. Stop at 70% (the lead's recommendation): keep what the runner does, amend ADR 25, and make the dry run and pages say so. Lead work runs while there's allowance and the reserve still protects planning. The cost is that a busy start can leave lead tickets stopped for days.
> 2. Follow the pace line: make the real pick obey ADR 25. The week spreads out, but at 61% used on 2026-11-04, lead tickets would have waited until about 7 Nov at 18:00 with allowance left.
>
> Whichever I choose:
> - A dry run and the runner must agree, with one shared function deciding whether a lead ticket may start. Add a test that gives both the same state and checks they give the same answer, including a week between the pace line and the reserve (61% against 32%).
> - runner/ is protected, so the runner change is the lead's ticket.
> - If a page changes what it shows, it needs the usual mock-up.

## The lead, 2026-11-04 21:02

> I've drafted ADR 44, a two-ticket plan and a mock-up, all assuming you choose to stop at 70%. If you choose the pace line, I'll rewrite the plan and f9-29 stays as it is.
>
> 1. **Your decision: stop at 70% or follow the pace line**: I recommend stopping at 70%, more firmly than your note does. No job would run differently from today. Following the line would have held 76 of the last 135 lead jobs (56%) with allowance left. It would also hold the wrong work: lead tickets cost $18 of $322 in the week of 26 Oct and $8 of $134 so far this week, and every other job would keep pushing the week past the line. The cost in your note is more than a 'can': the week reached 70% with four days or more to go in each of the last four weeks, and lead tickets then wait for the reset or the lever.
>    Action: Choose: (a) stop at 70%, as drafted in ADR 44, or (b) follow the pace line, and I rewrite the plan. If you just approve, I take that as (a).
> 2. **Coming, Overview and the factory line don't show the wrong wait**: Only the dry run does. Coming and the Overview call the dispatch code with empty windows and no tickets, so they can't show a pace wait; the factory line only reuses a pause word. The live Overview shows no wait on any lead row. They are wrong the other way: past 70%, a lead row still reads as next in line while the runner takes a developer's ticket, and nothing says lead tickets have stopped. The legend's 'the factory stops here' is also wrong for the week, because planning and reviews go on past the mark. F9's mock-up says the Tickets page shows 'over its pace line'. No page has that wording in its code; a job's page would only show it as a routing reason, and none has mentioned the pace line since 7 Oct.
>    Action: The Overview shows the real stop (points 6 and 8).
> 3. **Lead tickets were never paced for real, and ADR 25 misread the dry run**: f8-03 removed nothing: `_next_task` had the same rule before it. The rule dates from f1-46 (1 Oct), whose test says '0.5 on a Thursday is past the week's pace line, but not into the reserve' and lets the ticket run. The dry run has disagreed since f8-02 (5 Oct). On ADR 25's evening, five lead tickets (jobs 473 to 477) ran at 13% to 17% used, over that day's 11% line. When the 22:50 dry run was read, no run was going: run 152 had been interrupted at 22:34, and run 153 started at 23:42, a minute after ADR 25 was accepted. So the 15-hour hold it describes didn't come from the pace line.
>    Action: ADR 44 records this, and ADR 25 gets a line pointing at it.
> 4. **What the pace line still governs**: It still covers developer jobs on cloud agents through `router.route`, and paced windows such as Copilot's month. `allowance.answer` doesn't change, and the existing tests keep that path working. In practice it decides nothing today: no job's routing reason has mentioned the pace line since 7 Oct, and Claude last took a developer job on 2 Oct. It's worth keeping for when a cloud developer is listed, and F140, Copilot takes checkpoints first, plans to use it.
>    Action: Nothing to change.
> 5. **Neither option stops the week running out**: The week reached 99% or more between 3.5 and 4.8 days in, each of the last four weeks, and earlier every week, whatever lead tickets did. Planner replies are the cause: $214 of $322 in the week of 26 Oct. Those days without Claude cost you more than this card's question does. F177, Planner replies: record their real cost, start cold threads fresh, is already planned for this, but it sits with the cards at the back of the board.
>    Action: I suggest you drag F177 near the top of the board. No new card is needed.
> 6. **f9-29 is about to build the wrong page**: f9-29, the week pace ticket, is seventh in line, with five lead tickets ahead of it: perhaps two hours. It would draw 'Over pace: lead tickets wait until…', which isn't true. It's F9's ticket, so this plan can't change it until f219-02 runs. If it builds first, f219-02 writes a new ticket to replace what it drew, which pays for that page twice.
>    Action: When you approve, put F219 in the fast lane so it goes first. If you won't get to this in the next couple of hours, pause the factory from the top bar; you can still answer me here while it's paused.
> 7. **One function, and a test that the runner and dry run agree**: `allowance.lead_hold` decides, and the runner and the dry run both ask it, reading the windows the same way. The test covers 61% against 32%, 71%, 71% with the lever on, a fast lane card, and the 5-hour window at 80%, and checks both choose the same next ticket. I rejected the obvious fix of giving the real pick its windows: it would skip a held ticket, so it would never park and the desk item would never come.
>    Action: f219-01, a lead ticket since `runner/` is protected. Both tickets show 'relies on ADR 44' in the ticket check until the ADR is accepted; that's their only remaining problem.
> 8. **The Overview shows the stop, not a pace line**: The mock-up replaces F9's pace post. The week's mark says 'lead tickets stop here · planning and reviews go on'. Past it, a plate says until when, and each held lead row says it waits. You asked on 7 and 27 Oct to see when Claude's pacing happens. With this rule, the stop is what you'll see happening, and F61's 'at this rate' line gives the warning ahead of it.
>    Action: f219-02 rewrites f9-29 to this picture and corrects f61-01, f77-02 and their notes. Tell me if you'd still like a quiet pace post on the meter, but I'd leave it out: it would mark a line that holds nothing.
>
> Proposals:
> - ADR 44: Lead tickets stop at the reserve, not at the pace line (adr)
> - Where lead tickets stop, on the Overview (mockup)
> - F219: one rule for lead tickets (plan)

## The owner, 2026-11-04 22:02

> I want the pacing and the reserve, towards the end it can use the reserve if available. that was the original idea, why is it not followed. critical tickets will be added to the fast lane. why is dry run logic different than real logic, this seems like a smell. planning is the exception, it can still use the reserve

## The lead, 2026-11-04 22:06

> I've redrafted ADR 44, the two tickets and the mock-up to your rule: pacing, then the reserve at the end of the week, with planning exempt. Your questions are answered first, and three choices need you.
>
> 1. **Why the original idea wasn't followed**: It was written down but never built for lead tickets. ADR 15 paces every fixed window, Claude's week included, and ADR 25 kept that with a day's margin. The ticket that built the lead check, f1-46 (1 Oct), only said what to do when a job is refused because of the reserve. It said nothing about a refusal from the pace line, and its test then recorded the gap as correct: '0.5 on a Thursday is past the week's pace line, but not into the reserve'. My last reply treated that history as a reason to change the rule; your decision restores what you meant. I've replaced my recommendation.
>    Action: ADR 44 now enforces pacing for lead tickets rather than dropping it.
> 2. **Why the dry run differs from the real run: you're right, it's a smell**: Two pieces of code choose the next ticket. The real run uses `_next_task`, which only asks about the reserve. The dry run uses `dispatch.plan` with real windows, which applies the pace line. Since f8-03 the runner has given that same code empty windows, so its check only ever runs in the dry run. They also read the windows differently, and tell a lead ticket differently. The shared function you first asked for would have left the two paths in place, so the plan now goes further: the choice of next ticket becomes one function that both call, from the same windows.
>    Action: f219-01, plus the test you asked for, which gives both the same state.
> 3. **The cost: lead tickets will nearly stop until planner replies cost less**: I'm going with your rule, but you should know what it does at today's spend. The week is at 65% against a line of 33%, so lead tickets wait until about Sun 8 Nov 04:00, later if planning and reviews keep using the week. The line only rises about 0.42% an hour, and every job uses the same room. In the week of 26 Oct, planner replies and reviews cost $259 of $322, and lead tickets $18. 61 of the 105 ready tickets are lead tickets, and developer tickets that depend on them wait too. Your first priority is a runner that works by itself, so this works against it until planning costs less. Pacing lead tickets also won't stop the week running out, since they spend so little of it.
>    Action: Put F177, Planner replies: record their real cost, start cold threads fresh, in the fast lane along with this card. Its two lead tickets are the real fix, and they would otherwise wait behind this rule.
> 4. **'Towards the end': the last 17 hours, up to 90%**: I read this as the week's last 10%, the sweep ADR 15 already defines: from Sun 23:12 to the Monday 16:00 reset on this week's clock. A lead ticket may then use the reserve up to 90% of the week. The last 10%, about $32 or a dozen planner replies, stays so you can still plan. It wouldn't have mattered in the last four weeks: the week ran out 3.5 to 4.8 days in, before the last 10% began at 6.3 days.
>    Action: Choose: (a) last 10% of the week, up to 90% (my recommendation); (b) the same, up to 100%, which risks leaving no planning for the last hours; (c) the last full day instead.
> 5. **Are reviews, directions, escalations and checkpoints exempt too?**: You named planning as the exception, but today all of these skip the pace line and may use the reserve. I'd keep them that way. Directions and escalations rescue a stuck developer ticket, checkpoints cost about $1 a week, and pacing reviews would hold up your sign-offs. Reviews are the one with real savings, at $45 to $58 a week. That is F216, Let's redesign the milestone review's territory, so it's better cut there than delayed here.
>    Action: Choose: (a) all stay as today (my recommendation, as drafted); (b) pace reviews only; (c) pace all four, leaving planning as the only exception.
> 6. **A lead ticket held by the week waits by itself, with no desk item**: Today, at 70%, a lead ticket parks and asks you on your desk. Under your rule that would be wrong: it would never resume by itself in the last hours, and it would add an item every week. So it's passed over like a ticket waiting on a dependency, and starts when the line allows. The fast lane is your way past it, and the week's lever stays too. The 5-hour window doesn't change.
>    Action: This is in ADR 44, flagged because it changes ADR 15 and ADR 22's question. It's agreed unless you object.
> 7. **The Overview gets F9's pace post back, with two changes**: My last mock-up removed the post; it's back. The new mock-up shows real values: 65%, the post at 33%, the stripes, 'Over pace: lead tickets wait until about Sun 8 Nov 04:00', and each held lead row saying so. It adds a 'Last hours' plate, and corrects the mark's words, because planning and reviews go past it. The dry run no longer needs its own wording: the wait it prints comes from the same function.
>    Action: f219-02 points f9-29 at this picture. f61-01 and f77 go on waiting for f9-29 unchanged.
> 8. **What happens when you approve**: Once f219-01 merges, every lead ticket outside the fast lane stops until the line catches up, including f219-02 and f9-29. So until f9-29 lands, the Overview won't show why they wait; the runner's idle line will. If f9-29 runs before f219-01, which is possible with only four tickets ahead of it, the page would claim a wait that isn't real yet, for a short while; f219-02 would then fix any difference. No pause is needed.
>    Action: Accept ADR 44, approve the plan, and put F219 in the fast lane. Both tickets show 'relies on ADR 44' in the ticket check until the ADR is accepted; that's their only remaining problem.
>
> Proposals:
> - ADR 44: Lead tickets follow the pace line, and stop at the reserve until the week's end (adr)
> - Claude's week pace and reserve, on the Overview (mockup)
> - F219: lead tickets follow the pace, with one path for the runner and the dry run (plan)

## The owner, 2026-11-04 23:42

> I sent back your proposal “ADR 44: Lead tickets follow the pace line, and stop at the reserve until the week's end” (adr-44).
> - On its key point 3 (The reserve at the end of the week): go up to 100% on the last 17 hours, it'd be a shame to lose out on token, i may not do planning.

## The lead, 2026-11-04 23:43

> ADR 44, f219-01, the card and the mock-up now say up to 100% in the last 17 hours. All three proposals are listed again for you to approve.
>
> 1. **Up to 100% in the last 17 hours**: Done, and I agree: what's left at the reset is lost, and you're the one who knows whether you'll be planning. There is one risk: if lead tickets reach 100% before the reset, a planner reply waits for the reset too, and neither the lever nor the fast lane gets past a real limit. A lead ticket cut off by the limit parks and resumes after the reset, so its work isn't lost. In the last four weeks the week ran out before these hours began, so this only matters once the spend comes down.
>    Action: Changed in ADR 44 item 2, f219-01's tests, the card's D1 and D7, and the mock-up's Last hours plate.
> 2. **Your other choices, as I've taken them**: Reviews, directions, escalations and checkpoints stay as they are today: not paced, and may use the reserve. A lead ticket held by the week waits by itself, with no desk item. These are in the drafts as agreed.
>    Action: Nothing to do unless you disagree.
> 3. **When you approve**: Accept ADR 44 first, then approve the plan and put F219 in the fast lane. I still suggest putting F177, Planner replies: record their real cost, start cold threads fresh, in the fast lane with it, since it would otherwise wait behind this rule. Both tickets show 'relies on ADR 44' in the ticket check until the ADR is accepted; that's their only remaining problem.
>    Action: Accept and approve when you're ready.
>
> Proposals:
> - ADR 44: Lead tickets follow the pace line, and stop at the reserve until the week's end (adr)
> - Claude's week pace and reserve, on the Overview (mockup)
> - F219: lead tickets follow the pace, with one path for the runner and the dry run (plan)
