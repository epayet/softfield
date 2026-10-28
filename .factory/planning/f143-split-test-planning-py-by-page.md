# F143: Split the planning room's code and tests by page, so developers can take them

The planning thread behind F143's plan, oldest first, as it was when the owner approved it.

## The owner, 2026-10-24 00:32

> Plan this card.

## The lead, 2026-10-27 09:14

> I've planned F143 as five lead tickets on `plan/f143`. They split the planning room's code and its tests together. `softfield check-tickets` passes on all five, and there's no mock-up because nothing on screen changes.
>
> 1. **One file per page or per feature?**: Per page first, and per feature where a page would still be too big. A gate decides part of this: each test file must be named after a code file that exists (test_thread.py needs thread.py). So the 1,492-line planning.py has to be split along with its 4,441-line test file. That gives five pairs: the desk, the thread page, the proposal review page, and two features big enough to stand alone. Those are Coming (the Plant box, what's on its way, Didn't go through) and merge links. Your 'plant' joins Coming, since the Plant box is part of the desk. No test file will be over 1,500 lines. No rule or gate changes.
>    Action: Tickets f143-01 to f143-04, one move each; the layout is D1 in the card doc.
> 2. **Before or after the lead's tickets?**: Before. The 16 tickets have grown to 32 ready tickets that name these files: 20 are the lead's and 12 the developer's. The split only helps tickets that run after it. Since 2026-10-14, help for the developer stuck on these files (directions and escalations) has cost $12.83. Going first has one cost: each move must update the tickets that point at moved code in the same commit. Otherwise the runner's start-up check would reject them when they're picked. Each ticket does that.
>    Action: After you approve, drag F143 to sit just under F142, Why am I not getting notifications, above F15, Reprioritising tickets. Or tell me here if you'd rather it wait.
> 3. **The split helps, but it isn't the whole fix**: Developers also failed on tickets that spread over several pages (F172 touched seven files) and on the 2,172-line shared test setup file, conftest.py. So the split moves only two shared test fixtures into it. The last ticket rewrites F14's routing rule: one page's code, its test file and its template go to the developer; two pages' code, or a protected path, stay with the lead. It then moves the ready lead tickets that fit to the developer, but only those at difficulty 4 or below with no other reason to stay with the lead.
>    Action: Ticket f143-05 (the rule, the re-routing, and a check of the tickets the moves touched).
> 4. **Moves only, done by the lead**: These are five lead tickets that change no behaviour, page, name or test body. Each copies the file and deletes line ranges with sed rather than retyping thousands of lines. A move counts every line twice (removed and added), which goes over the 1,000-line diff limit, so each ticket raises its own limit (2,000 to 4,000). A developer can't do these: reading the big file is exactly what defeats them.
>    Action: Nothing more.
> 5. **Another card's ticket fails the start-up check**: f9-12-fix-the-desktop-test-does (F9) lists only tests but doesn't say tests_only: true. Approval and the runner will refuse it as it stands.
>    Action: I'll add tests_only: true to it at F9's next checkpoint or replan; this plan can't touch another card's ticket.
>
> Proposals:
> - F143: split the planning room's code and tests by page (plan)
