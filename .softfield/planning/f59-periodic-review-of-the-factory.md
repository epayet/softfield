# F59: A weekly report page: the factory's numbers over time and the lead's read

The planning thread behind F59's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-23 22:25

> I want a report page where I can read and browse previous reports. I'd say weekly, it could be a weekly task by the runner then the tokens are freshly back. I'm thinking something similar to /insights in principle but tailored to this factory. e can talk about what to put on there. Graphs over time would be nice. Jobs done by which agents, time spent, success rate, suggestions for improvement. It should have a global view and a per project view. I want to see how helpful the local agents are. Number of milestones done, where the tokens are being spent   give me more. Can start simple and add.more.larer

## The lead, 2026-10-26 23:12

> I've drafted the plan for F59 on its branch: four tickets, a mock-up of the new Reports page and the card's plan. Every number in the mock-up comes from the metrics database except the savings tile, which is made up; the four tickets pass the ticket check.
>
> 1. **The page works out the numbers; Claude writes only the words**: I'd change one thing in your idea. Claude shouldn't write the report's numbers each week. Everything you asked for is already in the metrics database: jobs by agent, time, success, dollars and milestones. So the page works them out every time it opens. That makes every week since 30 Sep readable as soon as it's built, the numbers can't drift from the data (planner answers have been wrong before when not read from the code), and a section added later shows for old weeks too. The weekly job writes only the read: what changed, whether it's good, what went wrong and its ideas, using the same numbers the page shows.
>    Action: Plan D1 and D3; ticket 01 works out the numbers.
> 2. **Weekly, right after Claude's weekly allowance comes back**: Agreed. Claude's seven-day allowance resets on Mondays at 16:00 UTC. At its first pick after that, the runner writes the report for the week just ended (Monday to Sunday, named by its Monday: "Week of 19 Oct"). It writes it once, even across restarts, on Opus. A review costs $1.83 on average, so a report should cost about $2–4 a week.
>    Action: Plan D2 and D6; ticket 03.
> 3. **Whole factory or one project, and the report is kept in the repo**: The page has a switch at the top: Whole factory, softfield, travel-companion. Each week's read is one file, .softfield/reports/<monday>.md, in Softfield's repo. It has a whole-factory section and a section for each project that ran jobs that week, and the page shows the section you chose. A file in git is backed up, and another frontier model can read it too.
>    Action: Plan D4 and D5.
> 4. **What the first version shows**: A strip of weeks you can browse (This week, numbers so far, then every past week), with the newest open. Then six tiles, each beside the week before: milestones done, tickets merged, Claude's dollars, the local developer's pass rate, timeouts (what F150 asked for before it was removed), and dollars saved by delegating. Then the lead's read with its ideas, and four graphs over the weeks: where Claude's dollars went, how often the local developer passed, hours by agent, and dollars beside milestones done. Last, a Who did what table.
>    Action: Plan D4; ticket 02 builds the page.
> 5. **How helpful the local developer is: the first answer**: Last week (19–25 Oct) Qwen passed 80 of its 104 attempts (77%), up from 36% the three weeks before, and timeouts fell from 14 to 4. By project it passed 88% on Travel companion (53 of 60) and 61% on Softfield (27 of 44). The report will show this every week, which also keeps answering F167 (Is the split between local developers and the lead smart and cheap?).
>    Action: Nothing now. Once the page is built, F167 can be archived with a link to it.
> 6. **Last week, planning cost more than building**: Planner replies took $149.80 of Claude's $305 (49%), which is more than lead tickets and reviews together ($135.60). That's 58 replies at $2.58 each. My guess is that each reply re-reads a long thread. The weekly read is meant to find things like this. Since it's already visible, I suggest planting it now: "Planner replies cost half of Claude's week (19 Oct: $150 of $305, $2.58 a reply): find what makes a reply cost that much and cut it, keeping planning on Opus."
>    Action: Paste that text into the Plant box if you agree.
> 7. **More to add later**: In the card's Later list, each one a section that will also show for past weeks: your own time (replies, approvals, how long things waited on your desk; F86, idea: tracking time the human spent on a project), planning rounds and dollars per approved plan, cost per merged ticket and per changed line by agent and project, ratings by kind of work (F80, Developer rating could be more tailored to the type of work), how much of each weekly allowance was used and when it ran out, why tickets were blocked, and the disk space the runs took (F175).
>    Action: These stay in the card's Later list; tell me which to bring into the first version.
> 8. **Ideas from the report can be planted**: The read writes each idea as a quoted line, the same form F164 (Plant a review's ideas straight from the review) uses. At first they show as plain quotes. A stretch ticket adds F164's Plant and Plant and ask the lead buttons once F164 is built.
>    Action: Plan D7; ticket 04 (stretch).
> 9. **Nothing on your desk**: A report asks nothing of you, so it never shows in Needs you or the notices. You open Reports when you want to.
>    Action: Plan D8.
> 10. **One more tab, and the Agents page overlaps**: Reports goes after Timeline, which makes 11 tabs. That's a lot on a phone. The Agents page's Efficiency table shows totals since the start with short headings, and Reports will cover most of it by week. I suggest keeping Agents for now. Once the ratings section (in Later) is on Reports, Agents can be folded into it.
>    Action: Nothing now; I'll raise it again when the ratings section is added.
> 11. **Who builds it, and when it runs**: Four tickets. 01 the local developer: the week's numbers, following the savings code. 02 the lead: the page and its graphs, because page and script work cost developers hours in F19 and F28. 03 the lead: the weekly job, in protected runner code, test-first. 04 the local developer: the Plant buttons, a stretch ticket that waits for F164. Ticket 02 also waits for F132 (The overview shows the whole factory), ticket 02. F59 sits near the end of the board (place 90), so drag it up if you want it sooner: at about 32 minutes a ticket, it's about two hours of work.
>    Action: Approve the plan to queue the tickets.
>
> Proposals:
> - F59: a Reports tab, one report a week (plan)
> - The Reports page, Today and Proposed (mockup)
