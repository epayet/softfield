# F228: The Overview and Milestones pages draw in about a second, softfield's too

The planning thread behind F228's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-11-05 11:03

> Loading the overview page is slow, especially for softfield

## The lead, 2026-11-05 11:31

> I timed the pages and found the cause. The plan is drafted as three tickets.
>
> 1. **How slow it is, and why softfield**: Softfield's Overview takes 6.6 s and coucou's 0.8 s, of which about 0.8 s is my measuring command starting up, so the live server should be a little quicker. About 4.6 s goes on the Claude per milestone chart. To draw it, the page works out the lead's rates again for each of softfield's 241 milestones, and each time it searches the whole jobs table once per merged lead ticket. Coucou has 6 milestones. This comes from reading the code and it fits the timings, but I haven't run a profiler.
>    Action: Ticket f228-01 works out the rates once. Ticket f228-03 adds indexes to the database.
> 2. **Milestones is worse, at 24 s**: The Milestones page does that same work five times, once for its table and once for each of its four charts, so it takes 24 s. You didn't mention this page, but it has the same cause and the same fix.
>    Action: Ticket f228-01 also makes Milestones do the work once.
> 3. **An open Overview keeps the machine busy**: The other 1 s or so comes from building the same data repeatedly: one load builds the factory floor four times and the board five. The 5-second refresh takes about 1.1 s of work each time and builds three floors and four boards, for as long as the page is open. That is roughly a fifth of one processor core per open tab. One copy of the top bar's desk count is even built and then thrown away.
>    Action: Ticket f228-02 builds each one once per request. Nothing is cached between requests, so nothing can go stale.
> 4. **Remove the chart instead? Not here**: You already decided on 2026-10-27 that this chart goes, and it would be tempting to just remove it now. I don't recommend that. Removing it wouldn't help Milestones, or the weekly report's savings, which use the same slow rates calculation, and it would clash with f132-04 in F132, One view of the whole factory, which already removes it. Fixing the calculation helps all of them, and the chart still goes with f132-04.
>    Action: No change to F132's tickets.
> 5. **Put this card ahead of F132**: f132-02 in F132, One view of the whole factory, makes the 5-second refresh cover every project. If it lands first, the repeated building described in point 3 happens for every project, not just one. It is #21 on the planted list, and new cards normally go after it. The two developer tickets don't use Claude's allowance while they run, which matters with the week at 91%. f228-03 is the lead's, so it follows Claude's week pace, but the two speed-ups don't wait for it.
>    Action: After you approve, drag F228 to the top of Planted, or at least above F132. If you leave it, it still gets built, just later.
> 6. **A bug set aside is replaced**: bug-36, "/live builds the board once", is a smaller part of point 3 and has been set aside as a seed. f228-02 does that work and more.
>    Action: Ticket f228-03 removes bug-36, so one less seed sits on the board.
> 7. **What this plan promises**: I expect about a second for both pages, but that is an estimate. f228-03 measures the same seven pages the same way and writes the figures on the card. If softfield's Overview still takes more than 2 s, it says what takes the time and proposes a fix. Automated tests count database queries and builds rather than seconds, because a time limit would fail whenever the machine is busy. Nothing on screen changes, so there is no mock-up.
>    Action: Ticket f228-03 records the figures.
>
> Proposals:
> - F228: the Overview and Milestones pages draw in about a second (plan)
